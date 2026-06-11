from __future__ import annotations

import math

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
    WavegenChannelLimits,
    WavegenConfig,
    WavegenLimits,
    WavegenStatus,
)

FAKE_DEFAULT_SAMPLE_RATE_HZ = 1000.0
FAKE_DEFAULT_SAMPLE_COUNT = 1000
FAKE_MAX_SAMPLE_COUNT_PER_CHANNEL = 32_768
FAKE_MAX_TOTAL_RETURNED_SAMPLES = 65_536
FAKE_DIGITAL_PIN_COUNT = 16
FAKE_DIGITAL_PIN_MASK = (1 << FAKE_DIGITAL_PIN_COUNT) - 1
FAKE_CUSTOM_WAVEGEN_SAMPLE_COUNT_MAX = 4096
FAKE_WAVEGEN_WAVEFORMS = ["sine", "square", "triangle", "dc", "custom"]
FAKE_WAVEGEN_LIMITS = WavegenChannelLimits(
    frequency_min_hz=0.1,
    frequency_max_hz=10_000_000.0,
    amplitude_min_v=0.0,
    amplitude_max_v=5.0,
    offset_min_v=-5.0,
    offset_max_v=5.0,
    duty_cycle_min_percent=0.0,
    duty_cycle_max_percent=100.0,
    custom_sample_count_min=2,
    custom_sample_count_max=FAKE_CUSTOM_WAVEGEN_SAMPLE_COUNT_MAX,
)


class FakeDwfAdapter:
    """Deterministic runtime backend for MCP demos without hardware."""

    def __init__(self) -> None:
        self._device = DeviceInfo(
            index=0,
            name="Analog Discovery 3 (Fake)",
            serial_number="FAKE-AD3-0001",
            available=True,
        )
        self._wavegen_state: dict[int, WavegenStatus] = {
            1: WavegenStatus(channel=1, state=0, running=False),
            2: WavegenStatus(channel=2, state=0, running=False),
        }
        self._digital_output_enable_mask = 0
        self._digital_output_mask = 0

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
        trigger_config: AnalogTriggerConfig | None = None,
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
        self._validate_device_index(device_index)
        return AnalogInputStatus(
            channel_count=2,
            frequency_min_hz=1.0,
            frequency_max_hz=100_000_000.0,
            current_frequency_hz=FAKE_DEFAULT_SAMPLE_RATE_HZ,
            buffer_size_min=1,
            buffer_size_max=FAKE_MAX_SAMPLE_COUNT_PER_CHANNEL,
            current_buffer_size=FAKE_DEFAULT_SAMPLE_COUNT,
            channel_ranges={"1": 5.0, "2": 5.0},
            channel_offsets={"1": 0.0, "2": 0.0},
            state=None,
        )

    def get_digital_io_limits(self, device_index: int) -> DigitalIOLimits:
        self._validate_device_index(device_index)
        supported_pins = list(range(FAKE_DIGITAL_PIN_COUNT))
        return DigitalIOLimits(
            supported_input_pins=supported_pins,
            supported_output_pins=supported_pins,
            input_mask=FAKE_DIGITAL_PIN_MASK,
            output_enable_mask=FAKE_DIGITAL_PIN_MASK,
        )

    def read_digital_inputs(self, device_index: int, pins: list[int]) -> DigitalInputRead:
        self._validate_device_index(device_index)
        input_mask = self._digital_output_mask & self._digital_output_enable_mask
        return DigitalInputRead(
            pins=pins,
            values=_digital_values(input_mask, pins),
            input_mask=input_mask,
        )

    def write_digital_outputs(
        self,
        device_index: int,
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
    ) -> DigitalOutputStatus:
        self._validate_device_index(device_index)
        selected_mask = _pins_to_mask(pins)
        values_mask = _pin_values_to_mask(pins, values)
        if preserve_existing:
            self._digital_output_enable_mask |= selected_mask
            self._digital_output_mask = (self._digital_output_mask & ~selected_mask) | values_mask
        else:
            self._digital_output_enable_mask = selected_mask
            self._digital_output_mask = values_mask
        self._digital_output_enable_mask &= FAKE_DIGITAL_PIN_MASK
        self._digital_output_mask &= FAKE_DIGITAL_PIN_MASK
        return DigitalOutputStatus(
            pins=pins,
            values=_digital_values(self._digital_output_mask, pins),
            output_enable_mask=self._digital_output_enable_mask,
            output_mask=self._digital_output_mask,
        )

    def get_wavegen_limits(self, device_index: int) -> WavegenLimits:
        self._validate_device_index(device_index)
        return WavegenLimits(
            supported_channels=[1, 2],
            supported_waveforms=FAKE_WAVEGEN_WAVEFORMS,
            default_waveform="sine",
            default_frequency_hz=1000.0,
            default_amplitude_v=1.0,
            default_offset_v=0.0,
            default_duty_cycle_percent=50.0,
            channel_limits={"1": FAKE_WAVEGEN_LIMITS, "2": FAKE_WAVEGEN_LIMITS},
        )

    def start_wavegen(self, device_index: int, config: WavegenConfig) -> WavegenStatus:
        self._validate_device_index(device_index)
        self._validate_wavegen_channel(config.channel)
        status = WavegenStatus(
            channel=config.channel,
            state=3,
            running=True,
            config=config,
        )
        self._wavegen_state[config.channel] = status
        return status

    def stop_wavegen(self, device_index: int, channel: int) -> WavegenStatus:
        self._validate_device_index(device_index)
        self._validate_wavegen_channel(channel)
        previous = self._wavegen_state[channel]
        status = WavegenStatus(
            channel=channel,
            state=2,
            running=False,
            config=previous.config,
        )
        self._wavegen_state[channel] = status
        return status

    def get_wavegen_status(self, device_index: int, channel: int) -> WavegenStatus:
        self._validate_device_index(device_index)
        self._validate_wavegen_channel(channel)
        return self._wavegen_state[channel]

    def _validate_device_index(self, device_index: int) -> None:
        if device_index != self._device.index:
            raise ValueError(f"No fake WaveForms device found at index {device_index}")

    def _validate_wavegen_channel(self, channel: int) -> None:
        if channel not in self._wavegen_state:
            raise ValueError("fake Wavegen channel must be 1 or 2")


def _fake_channel_samples(channel_index: int, sample_count: int) -> list[float]:
    if channel_index == 0:
        return [round(math.sin(index / 8.0), 6) for index in range(sample_count)]
    if channel_index == 1:
        return [round(0.5 * math.cos(index / 8.0), 6) for index in range(sample_count)]
    raise ValueError("fake analog channel index must be 0 or 1")


def _pins_to_mask(pins: list[int]) -> int:
    mask = 0
    for pin in pins:
        mask |= 1 << pin
    return mask


def _pin_values_to_mask(pins: list[int], values: list[bool]) -> int:
    mask = 0
    for pin, value in zip(pins, values, strict=True):
        if value:
            mask |= 1 << pin
    return mask


def _digital_values(mask: int, pins: list[int]) -> dict[str, bool]:
    return {str(pin): bool(mask & (1 << pin)) for pin in pins}
