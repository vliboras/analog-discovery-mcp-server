from __future__ import annotations

import math

from analog_discovery_mcp.models import AnalogCapture, AnalogCaptureLimits, DeviceInfo

FAKE_DEFAULT_SAMPLE_RATE_HZ = 1000.0
FAKE_DEFAULT_SAMPLE_COUNT = 1000
FAKE_MAX_SAMPLE_COUNT_PER_CHANNEL = 32_768
FAKE_MAX_TOTAL_RETURNED_SAMPLES = 65_536


class FakeDwfAdapter:
    """Deterministic runtime backend for MCP demos without hardware."""

    def __init__(self) -> None:
        self._device = DeviceInfo(
            index=0,
            name="Analog Discovery 3 (Fake)",
            serial_number="FAKE-AD3-0001",
            available=True,
        )

    def get_version(self) -> str:
        return "fake-0.1.0"

    def list_devices(self) -> list[DeviceInfo]:
        return [self._device]

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        if device_index != self._device.index:
            raise ValueError(f"No fake WaveForms device found at index {device_index}")
        if channel_index == 0:
            return 1.25
        if channel_index == 1:
            return 2.50
        raise ValueError("fake analog channel index must be 0 or 1")

    def get_analog_capture_limits(self, device_index: int) -> AnalogCaptureLimits:
        self._validate_device_index(device_index)
        return AnalogCaptureLimits(
            supported_channels=[1, 2],
            default_sample_rate_hz=FAKE_DEFAULT_SAMPLE_RATE_HZ,
            default_sample_count=FAKE_DEFAULT_SAMPLE_COUNT,
            max_sample_count_per_channel=FAKE_MAX_SAMPLE_COUNT_PER_CHANNEL,
            max_total_returned_samples=FAKE_MAX_TOTAL_RETURNED_SAMPLES,
        )

    def capture_analog_waveform(
        self,
        device_index: int,
        channel_indices: list[int],
        sample_rate_hz: float,
        sample_count: int,
    ) -> AnalogCapture:
        self._validate_device_index(device_index)
        samples = {
            str(channel_index + 1): _fake_channel_samples(channel_index, sample_count)
            for channel_index in channel_indices
        }
        return AnalogCapture(
            sample_rate_hz=sample_rate_hz,
            sample_count=sample_count,
            channels=[channel_index + 1 for channel_index in channel_indices],
            samples=samples,
        )

    def _validate_device_index(self, device_index: int) -> None:
        if device_index != self._device.index:
            raise ValueError(f"No fake WaveForms device found at index {device_index}")


def _fake_channel_samples(channel_index: int, sample_count: int) -> list[float]:
    if channel_index == 0:
        return [round(math.sin(index / 8.0), 6) for index in range(sample_count)]
    if channel_index == 1:
        return [round(0.5 * math.cos(index / 8.0), 6) for index in range(sample_count)]
    raise ValueError("fake analog channel index must be 0 or 1")
