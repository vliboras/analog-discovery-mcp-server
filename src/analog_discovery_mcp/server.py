from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar, cast

from mcp.server.fastmcp import FastMCP

from analog_discovery_mcp.dwf import DwfAdapter, LazyDwfAdapter
from analog_discovery_mcp.service import AnalogDiscoveryService

F = TypeVar("F", bound=Callable[..., object])


class ToolRegistrar(Protocol):
    def tool(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
        """Register a function as an MCP tool."""


def create_mcp_server(adapter: DwfAdapter | None = None) -> FastMCP:
    service = AnalogDiscoveryService(adapter or LazyDwfAdapter())
    mcp = FastMCP("Analog Discovery")
    register_tools(cast(ToolRegistrar, mcp), service)
    return mcp


def register_tools(mcp: ToolRegistrar, service: AnalogDiscoveryService) -> None:
    @mcp.tool()
    def get_waveforms_version() -> dict[str, object]:
        """Return the detected Digilent WaveForms SDK version."""

        return service.get_waveforms_version().model_dump(exclude_none=True)

    @mcp.tool()
    def list_devices() -> dict[str, object]:
        """List connected Digilent WaveForms devices."""

        return service.list_devices().model_dump(exclude_none=True)

    @mcp.tool()
    def read_analog_voltage(
        channel: int,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Read one analog input voltage sample from channel 1 or 2."""

        return service.read_analog_voltage(
            channel=channel,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)


def main() -> None:
    create_mcp_server().run()
