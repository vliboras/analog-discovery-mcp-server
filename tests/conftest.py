from __future__ import annotations

import os

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
    DigitalInputRead,
    DigitalIOLimits,
    DigitalOutputStatus,
    ReleaseDeviceStatus,
    WavegenChannelLimits,
    WavegenConfig,
    WavegenLimits,
    WavegenStatus,
)

ENV_HARDWARE_TESTS = "AD_MCP_HARDWARE_TESTS"
ENV_HARDWARE_STAND = "AD_MCP_HARDWARE_STAND"
DEFAULT_HARDWARE_STAND = "basic"
HARDWARE_STAND_ORDER = {
    "basic": 0,
    "advanced": 1,
}


def pytest_collection_modifyitems(config: pytest.Config, items: list[pytest.Item]) -> None:
    hardware_items = [item for item in items if "hardware" in item.keywords]
    if not hardware_items:
        return

    hardware_enabled = os.environ.get(ENV_HARDWARE_TESTS) == "1"
    selected_stand = os.environ.get(ENV_HARDWARE_STAND, DEFAULT_HARDWARE_STAND)
    if hardware_enabled and selected_stand not in HARDWARE_STAND_ORDER:
        raise pytest.UsageError(
            f"unknown {ENV_HARDWARE_STAND}={selected_stand!r}; expected one of: "
            f"{', '.join(HARDWARE_STAND_ORDER)}"
        )

    for item in hardware_items:
        if not hardware_enabled:
            item.add_marker(
                pytest.mark.skip(reason=f"set {ENV_HARDWARE_TESTS}=1 to run hardware tests")
            )
            continue

        stand_marker = item.get_closest_marker("hardware_stand")
        required_stand = (
            DEFAULT_HARDWARE_STAND
            if stand_marker is None
            else str(stand_marker.args[0])
        )
        if required_stand not in HARDWARE_STAND_ORDER:
            raise pytest.UsageError(
                f"unknown hardware_stand marker value {required_stand!r} on {item.nodeid}; "
                f"expected one of: {', '.join(HARDWARE_STAND_ORDER)}"
            )

        if not _stand_satisfies(selected_stand, required_stand):
            item.add_marker(
                pytest.mark.skip(
                    reason=(
                        f"requires {ENV_HARDWARE_STAND}={required_stand}; "
                        f"selected {selected_stand!r}"
                    )
                )
            )


def _stand_satisfies(selected_stand: str, required_stand: str) -> bool:
    return HARDWARE_STAND_ORDER[selected_stand] >= HARDWARE_STAND_ORDER[required_stand]


class RecordingDwfAdapter(DwfAdapter):
    def __init__(
        self,
        devices: list[DeviceInfo] | None = None,
        version: str = "3.24.3",
        read_voltage: float = 1.25,
        fail_version: Exception | None = None,
        fail_list: Exception | None = None,
        fail_read: Exception | None = None,
        fail_digital_limits: Exception | None = None,
        fail_digital_read: Exception | None = None,
        fail_digital_write: Exception | None = None,
    ) -> None:
        self.devices = devices or []
        self.version = version
        self.read_voltage_value = read_voltage
        self.fail_version = fail_version
        self.fail_list = fail_list
        self.fail_read = fail_read
        self.fail_digital_limits = fail_digital_limits
        self.fail_digital_read = fail_digital_read
        self.fail_digital_write = fail_digital_write
        self.read_calls: list[tuple[int, int]] = []
        self.capture_calls: list[
            tuple[int, list[int], float, int, AnalogTriggerConfig | None]
        ] = []
        self.wavegen_calls: list[tuple[str, int, object]] = []
        self.digital_calls: list[tuple[str, int, object]] = []
        self.digital_output_enable_mask = 0
        self.digital_output_mask = 0
        self.wavegen_state: dict[int, WavegenStatus] = {
            1: WavegenStatus(channel=1, state=0, running=False),
            2: WavegenStatus(channel=2, state=0, running=False),
        }

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

    def get_digital_io_limits(self, device_index: int) -> DigitalIOLimits:
        self.digital_calls.append(("limits", device_index, None))
        if self.fail_digital_limits:
            raise self.fail_digital_limits
        return DigitalIOLimits(
            supported_input_pins=list(range(16)),
            supported_output_pins=list(range(16)),
            input_mask=0xFFFF,
            output_enable_mask=0xFFFF,
        )

    def read_digital_inputs(self, device_index: int, pins: list[int]) -> DigitalInputRead:
        self.digital_calls.append(("read", device_index, pins))
        if self.fail_digital_read:
            raise self.fail_digital_read
        input_mask = self.digital_output_mask & self.digital_output_enable_mask
        return DigitalInputRead(
            pins=pins,
            values={str(pin): bool(input_mask & (1 << pin)) for pin in pins},
            input_mask=input_mask,
        )

    def write_digital_outputs(
        self,
        device_index: int,
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
    ) -> DigitalOutputStatus:
        self.digital_calls.append(
            ("write", device_index, (pins, values, preserve_existing))
        )
        if self.fail_digital_write:
            raise self.fail_digital_write
        selected_mask = sum(1 << pin for pin in pins)
        value_mask = sum(1 << pin for pin, value in zip(pins, values, strict=True) if value)
        if preserve_existing:
            self.digital_output_enable_mask |= selected_mask
            self.digital_output_mask = (self.digital_output_mask & ~selected_mask) | value_mask
        else:
            self.digital_output_enable_mask = selected_mask
            self.digital_output_mask = value_mask
        return DigitalOutputStatus(
            pins=pins,
            values={str(pin): bool(self.digital_output_mask & (1 << pin)) for pin in pins},
            output_enable_mask=self.digital_output_enable_mask,
            output_mask=self.digital_output_mask,
        )

    def get_wavegen_limits(self, device_index: int) -> WavegenLimits:
        limits = WavegenChannelLimits(
            frequency_min_hz=0.1,
            frequency_max_hz=10_000_000.0,
            amplitude_min_v=0.0,
            amplitude_max_v=5.0,
            offset_min_v=-5.0,
            offset_max_v=5.0,
            duty_cycle_min_percent=0.0,
            duty_cycle_max_percent=100.0,
            custom_sample_count_min=2,
            custom_sample_count_max=4096,
        )
        return WavegenLimits(
            supported_channels=[1, 2],
            supported_waveforms=["sine", "square", "triangle", "dc", "custom"],
            default_waveform="sine",
            default_frequency_hz=1000.0,
            default_amplitude_v=1.0,
            default_offset_v=0.0,
            default_duty_cycle_percent=50.0,
            channel_limits={"1": limits, "2": limits},
        )

    def start_wavegen(self, device_index: int, config: WavegenConfig) -> WavegenStatus:
        self.wavegen_calls.append(("start", device_index, config))
        status = WavegenStatus(
            channel=config.channel,
            state=3,
            running=True,
            config=config,
        )
        self.wavegen_state[config.channel] = status
        return status

    def start_synchronized_wavegen(
        self,
        device_index: int,
        configs: list[WavegenConfig],
        master_channel: int,
    ) -> list[WavegenStatus]:
        self.wavegen_calls.append(
            (
                "sync_start",
                device_index,
                {"configs": configs, "master_channel": master_channel},
            )
        )
        statuses: list[WavegenStatus] = []
        for config in configs:
            status = WavegenStatus(
                channel=config.channel,
                state=3,
                running=True,
                config=config,
            )
            self.wavegen_state[config.channel] = status
            statuses.append(status)
        return statuses

    def stop_wavegen(self, device_index: int, channel: int) -> WavegenStatus:
        self.wavegen_calls.append(("stop", device_index, channel))
        previous = self.wavegen_state[channel]
        status = WavegenStatus(
            channel=channel,
            state=2,
            running=False,
            config=previous.config,
        )
        self.wavegen_state[channel] = status
        return status

    def get_wavegen_status(self, device_index: int, channel: int) -> WavegenStatus:
        self.wavegen_calls.append(("status", device_index, channel))
        return self.wavegen_state[channel]

    def release_device(self, device_index: int) -> ReleaseDeviceStatus:
        self.wavegen_calls.append(("release", device_index, None))
        stopped_channels = [
            channel for channel, status in self.wavegen_state.items() if status.running
        ]
        for channel in stopped_channels:
            previous = self.wavegen_state[channel]
            self.wavegen_state[channel] = WavegenStatus(
                channel=channel,
                state=2,
                running=False,
                config=previous.config,
            )
        released = bool(stopped_channels) or self.digital_output_enable_mask != 0
        self.digital_output_enable_mask = 0
        self.digital_output_mask = 0
        return ReleaseDeviceStatus(
            released=released,
            wavegen_channels_stopped=sorted(stopped_channels),
            digital_output_enable_mask=0,
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
