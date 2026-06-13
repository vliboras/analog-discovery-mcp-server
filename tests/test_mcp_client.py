from __future__ import annotations

from pathlib import Path
from typing import Any

import anyio
from mcp import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

REPO_ROOT = Path(__file__).resolve().parents[1]


def test_mcp_client_can_call_fake_backend_tools() -> None:
    anyio.run(_call_fake_backend_tools)


async def _call_fake_backend_tools() -> None:
    server = StdioServerParameters(
        command="uv",
        args=["run", "analog-discovery-mcp-server"],
        env={"AD_MCP_DWF_BACKEND": "fake"},
        cwd=REPO_ROOT,
    )

    async with (
        stdio_client(server) as (read_stream, write_stream),
        ClientSession(read_stream, write_stream) as session,
    ):
        await session.initialize()

        tools = await session.list_tools()
        tool_names = {tool.name for tool in tools.tools}
        assert tool_names >= {
            "capture_analog_waveform",
            "get_analog_capture_limits",
            "get_analog_input_status",
            "get_wavegen_limits",
            "get_waveforms_version",
            "list_devices",
            "measure_analog_waveform",
            "release_device",
            "read_analog_voltage",
            "start_synchronized_wavegen",
            "start_wavegen",
            "stop_wavegen",
            "get_wavegen_status",
        }

        version = await session.call_tool("get_waveforms_version", {})
        assert _structured_content(version) == {
            "ok": True,
            "data": {"version": "fake-0.1.0"},
        }

        devices = await session.call_tool("list_devices", {})
        device_payload = _structured_content(devices)
        assert device_payload["ok"] is True
        assert device_payload["data"]["devices"][0]["name"] == "Analog Discovery 3 (Fake)"
        assert device_payload["data"]["devices"][0]["serial_number"] == "FAKE-AD3-0001"

        voltage = await session.call_tool("read_analog_voltage", {"channel": 2})
        voltage_payload = _structured_content(voltage)
        assert voltage_payload["ok"] is True
        assert voltage_payload["data"]["voltage"] == 2.5
        assert voltage_payload["data"]["channel"] == 2

        limits = await session.call_tool("get_analog_capture_limits", {})
        limits_payload = _structured_content(limits)
        assert limits_payload["ok"] is True
        assert limits_payload["data"]["max_sample_count_per_channel"] == 32_768

        capture = await session.call_tool(
            "capture_analog_waveform",
            {"channels": [1, 2], "sample_count": 8},
        )
        capture_payload = _structured_content(capture)
        assert capture_payload["ok"] is True
        assert capture_payload["data"]["channels"] == [1, 2]
        assert len(capture_payload["data"]["samples"]["1"]) == 8
        assert len(capture_payload["data"]["samples"]["2"]) == 8

        measurement = await session.call_tool(
            "measure_analog_waveform",
            {"channel": 1, "sample_count": 4},
        )
        measurement_payload = _structured_content(measurement)
        assert measurement_payload["ok"] is True
        assert "samples" not in measurement_payload["data"]
        assert measurement_payload["data"]["peak_to_peak_voltage"] > 0

        status = await session.call_tool("get_analog_input_status", {})
        status_payload = _structured_content(status)
        assert status_payload["ok"] is True
        assert status_payload["data"]["channel_count"] == 2

        wavegen_limits = await session.call_tool("get_wavegen_limits", {})
        wavegen_limits_payload = _structured_content(wavegen_limits)
        assert wavegen_limits_payload["ok"] is True
        assert wavegen_limits_payload["data"]["supported_waveforms"] == [
            "sine",
            "square",
            "triangle",
            "dc",
            "custom",
        ]

        wavegen_start = await session.call_tool(
            "start_wavegen",
            {"channel": 1, "waveform": "triangle", "frequency_hz": 2000.0},
        )
        wavegen_start_payload = _structured_content(wavegen_start)
        assert wavegen_start_payload["ok"] is True
        assert wavegen_start_payload["data"]["running"] is True
        assert wavegen_start_payload["data"]["config"]["waveform"] == "triangle"

        wavegen_status = await session.call_tool("get_wavegen_status", {"channel": 1})
        wavegen_status_payload = _structured_content(wavegen_status)
        assert wavegen_status_payload["ok"] is True
        assert wavegen_status_payload["data"]["running"] is True

        wavegen_custom = await session.call_tool(
            "start_wavegen",
            {
                "channel": 1,
                "waveform": "custom",
                "samples": [-1.0, 0.0, 1.0, 0.0],
                "sample_rate_hz": 4000.0,
            },
        )
        wavegen_custom_payload = _structured_content(wavegen_custom)
        assert wavegen_custom_payload["ok"] is True
        assert wavegen_custom_payload["data"]["config"]["waveform"] == "custom"
        assert wavegen_custom_payload["data"]["config"]["samples"] == [-1.0, 0.0, 1.0, 0.0]
        assert wavegen_custom_payload["data"]["config"]["frequency_hz"] == 1000.0

        synchronized_wavegen = await session.call_tool(
            "start_synchronized_wavegen",
            {
                "channels": [1, 2],
                "waveforms": ["sine", "sine"],
                "frequencies_hz": [1000.0, 1000.0],
                "amplitudes_v": [1.0, 1.0],
                "offsets_v": [0.0, 0.0],
                "phase_degrees": [0.0, 180.0],
            },
        )
        synchronized_wavegen_payload = _structured_content(synchronized_wavegen)
        assert synchronized_wavegen_payload["ok"] is True
        assert synchronized_wavegen_payload["data"]["synchronized"] is True
        assert synchronized_wavegen_payload["data"]["slave_channels"] == [2]
        second_sync_config = synchronized_wavegen_payload["data"]["statuses"][1]["config"]
        assert second_sync_config["phase_degrees"] == 180.0

        wavegen_stop = await session.call_tool("stop_wavegen", {"channel": 1})
        wavegen_stop_payload = _structured_content(wavegen_stop)
        assert wavegen_stop_payload["ok"] is True
        assert wavegen_stop_payload["data"]["running"] is False

        wavegen_stop_2 = await session.call_tool("stop_wavegen", {"channel": 2})
        wavegen_stop_2_payload = _structured_content(wavegen_stop_2)
        assert wavegen_stop_2_payload["ok"] is True
        assert wavegen_stop_2_payload["data"]["running"] is False

        release = await session.call_tool("release_device", {})
        release_payload = _structured_content(release)
        assert release_payload["ok"] is True
        assert release_payload["data"]["released"] is False


def _structured_content(result: Any) -> dict[str, Any]:
    content = result.structuredContent
    assert isinstance(content, dict)
    return content
