from __future__ import annotations

import pytest

from analog_discovery_mcp.adapters import DwfAdapter
from analog_discovery_mcp.dwf import DwfError
from analog_discovery_mcp.models import (
    AnalogCapture,
    AnalogCaptureLimits,
    AnalogInputStatus,
    AnalogStatusTime,
    AnalogTriggerConfig,
    DeviceInfo,
)


class FakeDwfAdapter(DwfAdapter):
    def __init__(
        self,
        devices: list[DeviceInfo] | None = None,
        version: str = "3.24.3",
        read_voltage: float = 1.25,
        fail_version: Exception | None = None,
        fail_list: Exception | None = None,
        fail_read: Exception | None = None,
    ) -> None:
        self.devices = devices or []
        self.version = version
        self.read_voltage_value = read_voltage
        self.fail_version = fail_version
        self.fail_list = fail_list
        self.fail_read = fail_read
        self.read_calls: list[tuple[int, int]] = []
        self.capture_calls: list[
            tuple[int, list[int], float, int, AnalogTriggerConfig | None]
        ] = []

    def get_version(self) -> str:
        if self.fail_version:
            raise self.fail_version
        return self.version

    def list_devices(self) -> list[DeviceInfo]:
        if self.fail_list:
            raise self.fail_list
        return self.devices

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        self.read_calls.append((device_index, channel_index))
        if self.fail_read:
            raise self.fail_read
        return self.read_voltage_value

    def get_analog_capture_limits(self, device_index: int) -> AnalogCaptureLimits:
        return AnalogCaptureLimits(
            supported_channels=[1, 2],
            default_sample_rate_hz=1000.0,
            default_sample_count=1000,
            max_sample_count_per_channel=32_768,
            max_total_returned_samples=65_536,
        )

    def capture_analog_waveform(
        self,
        device_index: int,
        channel_indices: list[int],
        sample_rate_hz: float,
        sample_count: int,
        trigger_config: AnalogTriggerConfig | None = None,
    ) -> AnalogCapture:
        self.capture_calls.append(
            (device_index, channel_indices, sample_rate_hz, sample_count, trigger_config)
        )
        return AnalogCapture(
            sample_rate_hz=sample_rate_hz,
            sample_count=sample_count,
            channels=[channel_index + 1 for channel_index in channel_indices],
            samples={
                str(channel_index + 1): [float(channel_index + 1)] * sample_count
                for channel_index in channel_indices
            },
            triggered=trigger_config is not None,
            auto_triggered=False if trigger_config is not None else None,
            valid_sample_count=sample_count,
            lost_sample_count=0,
            corrupt_sample_count=0,
            status_time=AnalogStatusTime(
                seconds_utc=0,
                tick=0,
                ticks_per_second=1_000_000,
            ),
            trigger=trigger_config,
        )

    def get_analog_input_status(self, device_index: int) -> AnalogInputStatus:
        return AnalogInputStatus(
            channel_count=2,
            frequency_min_hz=1.0,
            frequency_max_hz=100_000_000.0,
            current_frequency_hz=1000.0,
            buffer_size_min=1,
            buffer_size_max=32_768,
            current_buffer_size=1000,
            channel_ranges={"1": 5.0, "2": 5.0},
            channel_offsets={"1": 0.0, "2": 0.0},
            state=None,
        )


@pytest.fixture
def sample_devices() -> list[DeviceInfo]:
    return [
        DeviceInfo(index=0, name="Analog Discovery 2", serial_number="SN:AD2"),
        DeviceInfo(index=1, name="Analog Discovery 3", serial_number="SN:AD3"),
    ]


@pytest.fixture
def sdk_missing_error() -> DwfError:
    return DwfError("Unable to load WaveForms SDK library: libdwf.so")
