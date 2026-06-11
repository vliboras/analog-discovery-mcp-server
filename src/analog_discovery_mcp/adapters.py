from __future__ import annotations

from typing import Protocol

from analog_discovery_mcp.models import (
    AnalogCapture,
    AnalogCaptureLimits,
    AnalogInputStatus,
    AnalogTriggerConfig,
    DeviceInfo,
    DigitalInputRead,
    DigitalIOLimits,
    DigitalOutputStatus,
    WavegenConfig,
    WavegenLimits,
    WavegenStatus,
)


class DwfAdapter(Protocol):
    def get_version(self) -> str:
        """Return the WaveForms SDK version."""

    def list_devices(self) -> list[DeviceInfo]:
        """Return connected WaveForms devices."""

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        """Read one voltage sample from zero-based analog input channel."""

    def get_analog_capture_limits(self, device_index: int) -> AnalogCaptureLimits:
        """Return analog capture limits for the selected device."""

    def capture_analog_waveform(
        self,
        device_index: int,
        channel_indices: list[int],
        sample_rate_hz: float,
        sample_count: int,
        trigger_config: AnalogTriggerConfig | None = None,
    ) -> AnalogCapture:
        """Capture analog input waveform samples."""

    def get_analog_input_status(self, device_index: int) -> AnalogInputStatus:
        """Return analog input capability and current status metadata."""

    def get_digital_io_limits(self, device_index: int) -> DigitalIOLimits:
        """Return static digital I/O pin capabilities."""

    def read_digital_inputs(self, device_index: int, pins: list[int]) -> DigitalInputRead:
        """Read static digital input pin values."""

    def write_digital_outputs(
        self,
        device_index: int,
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
    ) -> DigitalOutputStatus:
        """Write static digital output pin values."""

    def get_wavegen_limits(self, device_index: int) -> WavegenLimits:
        """Return Wavegen limits for the selected device."""

    def start_wavegen(self, device_index: int, config: WavegenConfig) -> WavegenStatus:
        """Start analog output generation."""

    def stop_wavegen(self, device_index: int, channel: int) -> WavegenStatus:
        """Stop analog output generation."""

    def get_wavegen_status(self, device_index: int, channel: int) -> WavegenStatus:
        """Return analog output generation status."""
