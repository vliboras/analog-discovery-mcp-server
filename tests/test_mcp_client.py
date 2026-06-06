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
            "get_waveforms_version",
            "list_devices",
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


def _structured_content(result: Any) -> dict[str, Any]:
    content = result.structuredContent
    assert isinstance(content, dict)
    return content
