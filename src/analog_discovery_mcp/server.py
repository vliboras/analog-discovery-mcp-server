from __future__ import annotations

from collections.abc import Callable
from typing import Any, Protocol, TypeVar, cast

from mcp.server.fastmcp import FastMCP

from analog_discovery_mcp.adapters import DwfAdapter
from analog_discovery_mcp.backends import create_dwf_adapter
from analog_discovery_mcp.service import AnalogDiscoveryService

F = TypeVar("F", bound=Callable[..., object])


class ToolRegistrar(Protocol):
    def tool(self, *args: Any, **kwargs: Any) -> Callable[[F], F]:
        """Register a function as an MCP tool."""


def create_mcp_server(adapter: DwfAdapter | None = None) -> FastMCP:
    service = AnalogDiscoveryService(adapter or create_dwf_adapter())
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

    @mcp.tool()
    def get_analog_capture_limits(
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Return analog waveform capture limits for the selected device."""

        return service.get_analog_capture_limits(
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def capture_analog_waveform(
        channels: list[int] | None = None,
        sample_rate_hz: float = 1000.0,
        sample_count: int = 1000,
        device_index: int | None = None,
        serial_number: str | None = None,
        trigger_enabled: bool = False,
        trigger_channel: int | None = None,
        trigger_level_v: float = 0.0,
        trigger_edge: str = "rising",
        trigger_hysteresis_v: float = 0.05,
        trigger_auto_timeout_seconds: float = 1.0,
        trigger_position_seconds: float | None = None,
    ) -> dict[str, object]:
        """Capture analog input waveform samples from channel 1 and/or 2."""

        return service.capture_analog_waveform(
            channels=channels,
            sample_rate_hz=sample_rate_hz,
            sample_count=sample_count,
            device_index=device_index,
            serial_number=serial_number,
            trigger_enabled=trigger_enabled,
            trigger_channel=trigger_channel,
            trigger_level_v=trigger_level_v,
            trigger_edge=trigger_edge,
            trigger_hysteresis_v=trigger_hysteresis_v,
            trigger_auto_timeout_seconds=trigger_auto_timeout_seconds,
            trigger_position_seconds=trigger_position_seconds,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def measure_analog_waveform(
        channel: int,
        sample_rate_hz: float = 1000.0,
        sample_count: int = 1000,
        device_index: int | None = None,
        serial_number: str | None = None,
        trigger_enabled: bool = False,
        trigger_channel: int | None = None,
        trigger_level_v: float = 0.0,
        trigger_edge: str = "rising",
        trigger_hysteresis_v: float = 0.05,
        trigger_auto_timeout_seconds: float = 1.0,
        trigger_position_seconds: float | None = None,
    ) -> dict[str, object]:
        """Measure one channel; trigger_channel must match channel when provided."""

        return service.measure_analog_waveform(
            channel=channel,
            sample_rate_hz=sample_rate_hz,
            sample_count=sample_count,
            device_index=device_index,
            serial_number=serial_number,
            trigger_enabled=trigger_enabled,
            trigger_channel=trigger_channel,
            trigger_level_v=trigger_level_v,
            trigger_edge=trigger_edge,
            trigger_hysteresis_v=trigger_hysteresis_v,
            trigger_auto_timeout_seconds=trigger_auto_timeout_seconds,
            trigger_position_seconds=trigger_position_seconds,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def get_analog_input_status(
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Return analog input capability and current status metadata."""

        return service.get_analog_input_status(
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def get_digital_io_limits(
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Return static digital I/O pin capabilities."""

        return service.get_digital_io_limits(
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def read_digital_inputs(
        pins: list[int] | None = None,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Read static digital input pin values."""

        return service.read_digital_inputs(
            pins=pins,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def write_digital_outputs(
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Write static digital output pin values."""

        return service.write_digital_outputs(
            pins=pins,
            values=values,
            preserve_existing=preserve_existing,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def get_wavegen_limits(
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Return Wavegen output limits for the selected device."""

        return service.get_wavegen_limits(
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def start_wavegen(
        channel: int = 1,
        waveform: str = "sine",
        frequency_hz: float = 1000.0,
        amplitude_v: float = 1.0,
        offset_v: float = 0.0,
        duty_cycle_percent: float = 50.0,
        samples: list[float] | None = None,
        sample_rate_hz: float | None = None,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Start Wavegen output on a selected analog output channel."""

        return service.start_wavegen(
            channel=channel,
            waveform=waveform,
            frequency_hz=frequency_hz,
            amplitude_v=amplitude_v,
            offset_v=offset_v,
            duty_cycle_percent=duty_cycle_percent,
            samples=samples,
            sample_rate_hz=sample_rate_hz,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def start_synchronized_wavegen(
        channels: list[int] | None = None,
        waveforms: list[str] | None = None,
        frequencies_hz: list[float] | None = None,
        amplitudes_v: list[float] | None = None,
        offsets_v: list[float] | None = None,
        duty_cycles_percent: list[float] | None = None,
        phase_degrees: list[float] | None = None,
        master_channel: int = 1,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Start synchronized Wavegen outputs on multiple analog output channels."""

        return service.start_synchronized_wavegen(
            channels=channels,
            waveforms=waveforms,
            frequencies_hz=frequencies_hz,
            amplitudes_v=amplitudes_v,
            offsets_v=offsets_v,
            duty_cycles_percent=duty_cycles_percent,
            phase_degrees=phase_degrees,
            master_channel=master_channel,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def stop_wavegen(
        channel: int = 1,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Stop Wavegen output on a selected analog output channel."""

        return service.stop_wavegen(
            channel=channel,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def get_wavegen_status(
        channel: int = 1,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Return Wavegen status for a selected analog output channel."""

        return service.get_wavegen_status(
            channel=channel,
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)

    @mcp.tool()
    def release_device(
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> dict[str, object]:
        """Safely stop active outputs and release the selected device."""

        return service.release_device(
            device_index=device_index,
            serial_number=serial_number,
        ).model_dump(exclude_none=True)


def main() -> None:
    create_mcp_server().run()
