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
            "get_waveforms_version",
            "list_devices",
            "measure_analog_waveform",
            "read_analog_voltage",
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


def _structured_content(result: Any) -> dict[str, Any]:
    content = result.structuredContent
    assert isinstance(content, dict)
    return content
