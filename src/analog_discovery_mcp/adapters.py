from __future__ import annotations

from typing import Protocol

from analog_discovery_mcp.models import (
    AnalogCapture,
    AnalogCaptureLimits,
    AnalogInputStatus,
    AnalogTriggerConfig,
    DeviceInfo,
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
