from __future__ import annotations

import math
import os
from collections.abc import Mapping, Sequence
from dataclasses import asdict
from typing import TypeVar

from analog_discovery_mcp.adapters import DwfAdapter
from analog_discovery_mcp.dwf import DwfError
from analog_discovery_mcp.models import (
    AnalogCapture,
    AnalogCaptureLimits,
    AnalogTriggerConfig,
    DeviceInfo,
    DigitalIOLimits,
    ToolResult,
    WavegenChannelLimits,
    WavegenConfig,
    WavegenLimits,
    WavegenStatus,
)

ENV_DEVICE_INDEX = "AD_MCP_DEVICE_INDEX"
ENV_DEVICE_SERIAL = "AD_MCP_DEVICE_SERIAL"
DEFAULT_CAPTURE_CHANNELS = [1]
DEFAULT_CAPTURE_SAMPLE_RATE_HZ = 1000.0
DEFAULT_CAPTURE_SAMPLE_COUNT = 1000
DEFAULT_WAVEGEN_CHANNEL = 1
DEFAULT_WAVEGEN_WAVEFORM = "sine"
DEFAULT_WAVEGEN_FREQUENCY_HZ = 1000.0
DEFAULT_WAVEGEN_AMPLITUDE_V = 1.0
DEFAULT_WAVEGEN_OFFSET_V = 0.0
DEFAULT_WAVEGEN_DUTY_CYCLE_PERCENT = 50.0
DEFAULT_SYNC_WAVEGEN_CHANNELS = [1, 2]
DEFAULT_SYNC_WAVEGEN_PHASE_DEGREES = [0.0, 180.0]
T = TypeVar("T")


class AnalogDiscoveryService:
    def __init__(self, adapter: DwfAdapter, environ: Mapping[str, str] | None = None) -> None:
        self._adapter = adapter
        self._environ = os.environ if environ is None else environ

    def get_waveforms_version(self) -> ToolResult:
        try:
            return ToolResult(ok=True, data={"version": self._adapter.get_version()})
        except DwfError as exc:
            return ToolResult(ok=False, error=str(exc))

    def list_devices(self) -> ToolResult:
        try:
            devices = [asdict(device) for device in self._adapter.list_devices()]
            return ToolResult(ok=True, data={"devices": devices})
        except DwfError as exc:
            return ToolResult(ok=False, error=str(exc))

    def read_analog_voltage(
        self,
        channel: int,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        if channel not in (1, 2):
            return ToolResult(ok=False, error="channel must be 1 or 2")

        try:
            selected_device = self._select_device(device_index, serial_number)
            voltage = self._adapter.read_analog_voltage(
                device_index=selected_device.index,
                channel_index=channel - 1,
            )
            return ToolResult(
                ok=True,
                data={
                    "voltage": voltage,
                    "unit": "V",
                    "channel": channel,
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def get_analog_capture_limits(
        self,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_analog_capture_limits(selected_device.index)
            return ToolResult(
                ok=True,
                data={
                    **asdict(limits),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def capture_analog_waveform(
        self,
        channels: list[int] | None = None,
        sample_rate_hz: float = DEFAULT_CAPTURE_SAMPLE_RATE_HZ,
        sample_count: int = DEFAULT_CAPTURE_SAMPLE_COUNT,
        device_index: int | None = None,
        serial_number: str | None = None,
        trigger_enabled: bool = False,
        trigger_channel: int | None = None,
        trigger_level_v: float = 0.0,
        trigger_edge: str = "rising",
        trigger_hysteresis_v: float = 0.05,
        trigger_auto_timeout_seconds: float = 1.0,
        trigger_position_seconds: float | None = None,
    ) -> ToolResult:
        requested_channels = DEFAULT_CAPTURE_CHANNELS if channels is None else channels

        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_analog_capture_limits(selected_device.index)
            _validate_capture_request(
                requested_channels,
                sample_rate_hz,
                sample_count,
                limits,
            )
            trigger_config = _build_trigger_config(
                trigger_enabled=trigger_enabled,
                trigger_channel=trigger_channel,
                requested_channels=requested_channels,
                sample_rate_hz=sample_rate_hz,
                sample_count=sample_count,
                limits=limits,
                trigger_level_v=trigger_level_v,
                trigger_edge=trigger_edge,
                trigger_hysteresis_v=trigger_hysteresis_v,
                trigger_auto_timeout_seconds=trigger_auto_timeout_seconds,
                trigger_position_seconds=trigger_position_seconds,
            )
            capture = self._adapter.capture_analog_waveform(
                device_index=selected_device.index,
                channel_indices=[channel - 1 for channel in requested_channels],
                sample_rate_hz=sample_rate_hz,
                sample_count=sample_count,
                trigger_config=trigger_config,
            )
            return ToolResult(
                ok=True,
                data=_capture_payload(capture, sample_rate_hz, selected_device),
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def measure_analog_waveform(
        self,
        channel: int,
        sample_rate_hz: float = DEFAULT_CAPTURE_SAMPLE_RATE_HZ,
        sample_count: int = DEFAULT_CAPTURE_SAMPLE_COUNT,
        device_index: int | None = None,
        serial_number: str | None = None,
        trigger_enabled: bool = False,
        trigger_channel: int | None = None,
        trigger_level_v: float = 0.0,
        trigger_edge: str = "rising",
        trigger_hysteresis_v: float = 0.05,
        trigger_auto_timeout_seconds: float = 1.0,
        trigger_position_seconds: float | None = None,
    ) -> ToolResult:
        result = self.capture_analog_waveform(
            channels=[channel],
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
        )
        if not result.ok or result.data is None:
            return result

        samples = result.data["samples"][str(channel)]
        stats = _measure_samples(samples)
        payload = {
            key: value
            for key, value in result.data.items()
            if key != "samples"
        }
        payload.update(
            {
                "channel": channel,
                **stats,
            }
        )
        return ToolResult(ok=True, data=payload)

    def get_analog_input_status(
        self,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            status = self._adapter.get_analog_input_status(selected_device.index)
            return ToolResult(
                ok=True,
                data={
                    **asdict(status),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def get_digital_io_limits(
        self,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_digital_io_limits(selected_device.index)
            return ToolResult(
                ok=True,
                data={
                    **asdict(limits),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def read_digital_inputs(
        self,
        pins: list[int] | None = None,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_digital_io_limits(selected_device.index)
            requested_pins = limits.supported_input_pins if pins is None else pins
            _validate_digital_pins(
                "pins",
                requested_pins,
                limits.supported_input_pins,
            )
            read = self._adapter.read_digital_inputs(selected_device.index, requested_pins)
            return ToolResult(
                ok=True,
                data={
                    **asdict(read),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def write_digital_outputs(
        self,
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_digital_io_limits(selected_device.index)
            _validate_digital_write_request(pins, values, limits)
            status = self._adapter.write_digital_outputs(
                selected_device.index,
                pins,
                values,
                preserve_existing,
            )
            return ToolResult(
                ok=True,
                data={
                    **asdict(status),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def get_wavegen_limits(
        self,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_wavegen_limits(selected_device.index)
            return ToolResult(
                ok=True,
                data={
                    **asdict(limits),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def start_wavegen(
        self,
        channel: int = DEFAULT_WAVEGEN_CHANNEL,
        waveform: str = DEFAULT_WAVEGEN_WAVEFORM,
        frequency_hz: float = DEFAULT_WAVEGEN_FREQUENCY_HZ,
        amplitude_v: float = DEFAULT_WAVEGEN_AMPLITUDE_V,
        offset_v: float = DEFAULT_WAVEGEN_OFFSET_V,
        duty_cycle_percent: float = DEFAULT_WAVEGEN_DUTY_CYCLE_PERCENT,
        samples: list[float] | None = None,
        sample_rate_hz: float | None = None,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_wavegen_limits(selected_device.index)
            config = _build_wavegen_config(
                channel=channel,
                waveform=waveform,
                frequency_hz=frequency_hz,
                amplitude_v=amplitude_v,
                offset_v=offset_v,
                duty_cycle_percent=duty_cycle_percent,
                phase_degrees=None,
                samples=samples,
                sample_rate_hz=sample_rate_hz,
                limits=limits,
            )
            status = self._adapter.start_wavegen(selected_device.index, config)
            return ToolResult(
                ok=True,
                data=_wavegen_status_payload(status, selected_device),
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def start_synchronized_wavegen(
        self,
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
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_wavegen_limits(selected_device.index)
            configs = _build_synchronized_wavegen_configs(
                channels=channels,
                waveforms=waveforms,
                frequencies_hz=frequencies_hz,
                amplitudes_v=amplitudes_v,
                offsets_v=offsets_v,
                duty_cycles_percent=duty_cycles_percent,
                phase_degrees=phase_degrees,
                master_channel=master_channel,
                limits=limits,
            )
            statuses = self._adapter.start_synchronized_wavegen(
                selected_device.index,
                configs,
                master_channel,
            )
            return ToolResult(
                ok=True,
                data=_synchronized_wavegen_payload(statuses, master_channel, selected_device),
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def stop_wavegen(
        self,
        channel: int = DEFAULT_WAVEGEN_CHANNEL,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_wavegen_limits(selected_device.index)
            _validate_wavegen_channel(channel, limits)
            status = self._adapter.stop_wavegen(selected_device.index, channel)
            return ToolResult(
                ok=True,
                data=_wavegen_status_payload(status, selected_device),
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def get_wavegen_status(
        self,
        channel: int = DEFAULT_WAVEGEN_CHANNEL,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_wavegen_limits(selected_device.index)
            _validate_wavegen_channel(channel, limits)
            status = self._adapter.get_wavegen_status(selected_device.index, channel)
            return ToolResult(
                ok=True,
                data=_wavegen_status_payload(status, selected_device),
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def release_device(
        self,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            status = self._adapter.release_device(selected_device.index)
            return ToolResult(
                ok=True,
                data={
                    **asdict(status),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def _select_device(
        self,
        device_index: int | None,
        serial_number: str | None,
    ) -> DeviceInfo:
        requested_index, requested_serial = self._resolve_selection(device_index, serial_number)
        devices = self._adapter.list_devices()

        if not devices:
            raise ValueError("No WaveForms devices found")

        if requested_serial is not None:
            for device in devices:
                if device.serial_number == requested_serial:
                    return device
            raise ValueError(f"No WaveForms device found with serial number {requested_serial!r}")

        if requested_index is None:
            requested_index = 0

        for device in devices:
            if device.index == requested_index:
                return device

        raise ValueError(f"No WaveForms device found at index {requested_index}")

    def _resolve_selection(
        self,
        device_index: int | None,
        serial_number: str | None,
    ) -> tuple[int | None, str | None]:
        if device_index is not None and serial_number:
            raise ValueError("Use either device_index or serial_number, not both")

        env_index = self._environ.get(ENV_DEVICE_INDEX)
        env_serial = self._environ.get(ENV_DEVICE_SERIAL)

        if device_index is not None or serial_number:
            return device_index, serial_number

        if env_index and env_serial:
            raise ValueError(f"Set only one of {ENV_DEVICE_INDEX} or {ENV_DEVICE_SERIAL}")

        if env_serial:
            return None, env_serial

        if env_index:
            try:
                return int(env_index), None
            except ValueError as exc:
                raise ValueError(f"{ENV_DEVICE_INDEX} must be an integer") from exc

        return None, None


def _validate_capture_request(
    channels: list[int],
    sample_rate_hz: float,
    sample_count: int,
    limits: AnalogCaptureLimits,
) -> None:
    if not channels:
        raise ValueError("channels must not be empty")

    if len(set(channels)) != len(channels):
        raise ValueError("channels must not contain duplicates")

    unsupported_channels = sorted(set(channels) - set(limits.supported_channels))
    if unsupported_channels:
        raise ValueError(
            "channels must only contain supported channels "
            f"{limits.supported_channels}; got {unsupported_channels}"
        )

    if sample_rate_hz <= 0:
        raise ValueError("sample_rate_hz must be positive")

    if sample_count < 1 or sample_count > limits.max_sample_count_per_channel:
        raise ValueError(
            f"sample_count must be between 1 and {limits.max_sample_count_per_channel}"
        )

    total_samples = len(channels) * sample_count
    if total_samples > limits.max_total_returned_samples:
        raise ValueError(
            f"total returned samples must be at most {limits.max_total_returned_samples}"
        )


def _validate_digital_write_request(
    pins: list[int],
    values: list[bool],
    limits: DigitalIOLimits,
) -> None:
    _validate_digital_pins("pins", pins, limits.supported_output_pins)
    if len(values) != len(pins):
        raise ValueError("values length must match pins length")
    if not all(isinstance(value, bool) for value in values):
        raise ValueError("values must contain booleans")


def _validate_digital_pins(name: str, pins: list[int], supported_pins: list[int]) -> None:
    if not pins:
        raise ValueError(f"{name} must not be empty")

    if len(set(pins)) != len(pins):
        raise ValueError(f"{name} must not contain duplicates")

    unsupported_pins = sorted(set(pins) - set(supported_pins))
    if unsupported_pins:
        raise ValueError(
            f"{name} must only contain supported pins {supported_pins}; got {unsupported_pins}"
        )


def _build_trigger_config(
    *,
    trigger_enabled: bool,
    trigger_channel: int | None,
    requested_channels: list[int],
    sample_rate_hz: float,
    sample_count: int,
    limits: AnalogCaptureLimits,
    trigger_level_v: float,
    trigger_edge: str,
    trigger_hysteresis_v: float,
    trigger_auto_timeout_seconds: float,
    trigger_position_seconds: float | None,
) -> AnalogTriggerConfig | None:
    if not trigger_enabled:
        return None

    channel = requested_channels[0] if trigger_channel is None else trigger_channel
    if channel not in limits.supported_channels:
        raise ValueError(f"trigger_channel must be one of {limits.supported_channels}")
    if channel not in requested_channels:
        raise ValueError("trigger_channel must be included in channels")

    edge = trigger_edge.strip().lower()
    if edge not in ("rising", "falling"):
        raise ValueError("trigger_edge must be 'rising' or 'falling'")

    if not math.isfinite(trigger_level_v):
        raise ValueError("trigger_level_v must be finite")
    if not math.isfinite(trigger_hysteresis_v) or trigger_hysteresis_v <= 0:
        raise ValueError("trigger_hysteresis_v must be positive")
    if not math.isfinite(trigger_auto_timeout_seconds) or trigger_auto_timeout_seconds <= 0:
        raise ValueError("trigger_auto_timeout_seconds must be positive")

    duration_seconds = sample_count / sample_rate_hz
    position_seconds = (
        duration_seconds / 2 if trigger_position_seconds is None else trigger_position_seconds
    )
    if (
        not math.isfinite(position_seconds)
        or position_seconds < 0
        or position_seconds > duration_seconds
    ):
        raise ValueError(
            f"trigger_position_seconds must be between 0 and {duration_seconds}"
        )

    return AnalogTriggerConfig(
        channel=channel,
        level_v=trigger_level_v,
        edge=edge,
        hysteresis_v=trigger_hysteresis_v,
        auto_timeout_seconds=trigger_auto_timeout_seconds,
        position_seconds=position_seconds,
    )


def _capture_payload(
    capture: AnalogCapture,
    requested_sample_rate_hz: float,
    selected_device: DeviceInfo,
) -> dict[str, object]:
    return {
        "requested_sample_rate_hz": requested_sample_rate_hz,
        "actual_sample_rate_hz": capture.sample_rate_hz,
        "sample_count": capture.sample_count,
        "duration_seconds": capture.sample_count / capture.sample_rate_hz,
        "channels": capture.channels,
        "samples": capture.samples,
        "triggered": capture.triggered,
        "auto_triggered": capture.auto_triggered,
        "valid_sample_count": capture.valid_sample_count,
        "lost_sample_count": capture.lost_sample_count,
        "corrupt_sample_count": capture.corrupt_sample_count,
        "status_time": asdict(capture.status_time) if capture.status_time else None,
        "trigger": asdict(capture.trigger) if capture.trigger else None,
        "device": asdict(selected_device),
    }


def _measure_samples(samples: list[float]) -> dict[str, float]:
    if not samples:
        raise ValueError("samples must not be empty")

    mean = sum(samples) / len(samples)
    rms = math.sqrt(sum(sample * sample for sample in samples) / len(samples))
    min_voltage = min(samples)
    max_voltage = max(samples)
    return {
        "min_voltage": min_voltage,
        "max_voltage": max_voltage,
        "mean_voltage": mean,
        "rms_voltage": rms,
        "peak_to_peak_voltage": max_voltage - min_voltage,
    }


def _build_wavegen_config(
    *,
    channel: int,
    waveform: str,
    frequency_hz: float,
    amplitude_v: float,
    offset_v: float,
    duty_cycle_percent: float,
    phase_degrees: float | None,
    samples: list[float] | None,
    sample_rate_hz: float | None,
    limits: WavegenLimits,
) -> WavegenConfig:
    _validate_wavegen_channel(channel, limits)

    normalized_waveform = waveform.strip().lower()
    if normalized_waveform not in limits.supported_waveforms:
        raise ValueError(
            "waveform must be one of "
            f"{limits.supported_waveforms}; got {waveform!r}"
        )

    for name, value in _wavegen_numeric_values(
        frequency_hz=frequency_hz,
        amplitude_v=amplitude_v,
        offset_v=offset_v,
        duty_cycle_percent=duty_cycle_percent,
        phase_degrees=phase_degrees,
        sample_rate_hz=sample_rate_hz,
    ).items():
        if not math.isfinite(value):
            raise ValueError(f"{name} must be finite")

    channel_limits = _wavegen_channel_limits(channel, limits)
    _validate_range(
        "offset_v",
        offset_v,
        channel_limits.offset_min_v,
        channel_limits.offset_max_v,
    )
    if phase_degrees is not None:
        _validate_range(
            "phase_degrees",
            phase_degrees,
            channel_limits.phase_min_degrees,
            channel_limits.phase_max_degrees,
        )

    if normalized_waveform == "custom":
        if samples is None:
            raise ValueError("samples are required for custom waveform")
        if sample_rate_hz is None:
            raise ValueError("sample_rate_hz is required for custom waveform")
        _validate_range(
            "amplitude_v",
            amplitude_v,
            channel_limits.amplitude_min_v,
            channel_limits.amplitude_max_v,
        )
        custom_samples = _validate_custom_wavegen_samples(samples, channel_limits)
        custom_frequency_hz = sample_rate_hz / len(custom_samples)
        _validate_range(
            "sample_rate_hz / len(samples)",
            custom_frequency_hz,
            channel_limits.frequency_min_hz,
            channel_limits.frequency_max_hz,
        )
        return WavegenConfig(
            channel=channel,
            waveform=normalized_waveform,
            frequency_hz=custom_frequency_hz,
            amplitude_v=amplitude_v,
            offset_v=offset_v,
            duty_cycle_percent=duty_cycle_percent,
            phase_degrees=phase_degrees,
            samples=custom_samples,
            sample_rate_hz=sample_rate_hz,
        )

    if samples is not None:
        raise ValueError("samples are only supported for custom waveform")
    if sample_rate_hz is not None:
        raise ValueError("sample_rate_hz is only supported for custom waveform")

    if normalized_waveform == "dc":
        return WavegenConfig(
            channel=channel,
            waveform=normalized_waveform,
            frequency_hz=frequency_hz,
            amplitude_v=0.0,
            offset_v=offset_v,
            duty_cycle_percent=duty_cycle_percent,
            phase_degrees=phase_degrees,
        )

    _validate_range(
        "frequency_hz",
        frequency_hz,
        channel_limits.frequency_min_hz,
        channel_limits.frequency_max_hz,
    )
    _validate_range(
        "amplitude_v",
        amplitude_v,
        channel_limits.amplitude_min_v,
        channel_limits.amplitude_max_v,
    )
    _validate_range(
        "duty_cycle_percent",
        duty_cycle_percent,
        channel_limits.duty_cycle_min_percent,
        channel_limits.duty_cycle_max_percent,
    )

    return WavegenConfig(
        channel=channel,
        waveform=normalized_waveform,
        frequency_hz=frequency_hz,
        amplitude_v=amplitude_v,
        offset_v=offset_v,
        duty_cycle_percent=duty_cycle_percent,
        phase_degrees=phase_degrees,
    )


def _build_synchronized_wavegen_configs(
    *,
    channels: list[int] | None,
    waveforms: list[str] | None,
    frequencies_hz: list[float] | None,
    amplitudes_v: list[float] | None,
    offsets_v: list[float] | None,
    duty_cycles_percent: list[float] | None,
    phase_degrees: list[float] | None,
    master_channel: int,
    limits: WavegenLimits,
) -> list[WavegenConfig]:
    requested_channels = DEFAULT_SYNC_WAVEGEN_CHANNELS if channels is None else channels
    if not requested_channels:
        raise ValueError("channels must not be empty")
    if len(set(requested_channels)) != len(requested_channels):
        raise ValueError("channels must not contain duplicates")
    if master_channel not in requested_channels:
        raise ValueError("master_channel must be included in channels")

    _validate_parallel_length("waveforms", waveforms, requested_channels)
    _validate_parallel_length("frequencies_hz", frequencies_hz, requested_channels)
    _validate_parallel_length("amplitudes_v", amplitudes_v, requested_channels)
    _validate_parallel_length("offsets_v", offsets_v, requested_channels)
    _validate_parallel_length("duty_cycles_percent", duty_cycles_percent, requested_channels)
    _validate_parallel_length("phase_degrees", phase_degrees, requested_channels)

    default_phases = (
        DEFAULT_SYNC_WAVEGEN_PHASE_DEGREES
        if len(requested_channels) == len(DEFAULT_SYNC_WAVEGEN_PHASE_DEGREES)
        else [0.0 for _channel in requested_channels]
    )
    configs: list[WavegenConfig] = []
    for index, channel in enumerate(requested_channels):
        waveform = _parallel_value(waveforms, index, DEFAULT_WAVEGEN_WAVEFORM)
        if waveform.strip().lower() == "custom":
            raise ValueError("custom waveform is not supported by start_synchronized_wavegen")
        config = _build_wavegen_config(
            channel=channel,
            waveform=waveform,
            frequency_hz=_parallel_value(
                frequencies_hz,
                index,
                DEFAULT_WAVEGEN_FREQUENCY_HZ,
            ),
            amplitude_v=_parallel_value(
                amplitudes_v,
                index,
                DEFAULT_WAVEGEN_AMPLITUDE_V,
            ),
            offset_v=_parallel_value(offsets_v, index, DEFAULT_WAVEGEN_OFFSET_V),
            duty_cycle_percent=_parallel_value(
                duty_cycles_percent,
                index,
                DEFAULT_WAVEGEN_DUTY_CYCLE_PERCENT,
            ),
            phase_degrees=_parallel_value(phase_degrees, index, default_phases[index]),
            samples=None,
            sample_rate_hz=None,
            limits=limits,
        )
        configs.append(config)
    return configs


def _validate_parallel_length(
    name: str,
    values: Sequence[object] | None,
    channels: list[int],
) -> None:
    if values is not None and len(values) != len(channels):
        raise ValueError(f"{name} length must match channels length")


def _parallel_value(values: Sequence[T] | None, index: int, default: T) -> T:
    if values is None:
        return default
    return values[index]


def _validate_wavegen_channel(channel: int, limits: WavegenLimits) -> None:
    if channel not in limits.supported_channels:
        raise ValueError(
            f"channel must be one of {limits.supported_channels}; got {channel}"
        )


def _wavegen_numeric_values(
    *,
    frequency_hz: float,
    amplitude_v: float,
    offset_v: float,
    duty_cycle_percent: float,
    phase_degrees: float | None,
    sample_rate_hz: float | None,
) -> dict[str, float]:
    values = {
        "frequency_hz": frequency_hz,
        "amplitude_v": amplitude_v,
        "offset_v": offset_v,
        "duty_cycle_percent": duty_cycle_percent,
    }
    if phase_degrees is not None:
        values["phase_degrees"] = phase_degrees
    if sample_rate_hz is not None:
        values["sample_rate_hz"] = sample_rate_hz
    return values


def _validate_custom_wavegen_samples(
    samples: list[float],
    channel_limits: WavegenChannelLimits,
) -> list[float]:
    sample_count = len(samples)
    minimum = channel_limits.custom_sample_count_min
    maximum = channel_limits.custom_sample_count_max
    if minimum is None or maximum is None:
        raise ValueError("selected device does not support custom Wavegen samples")
    if sample_count < minimum or sample_count > maximum:
        raise ValueError(f"samples length must be between {minimum} and {maximum}")

    validated: list[float] = []
    for sample in samples:
        if not math.isfinite(sample):
            raise ValueError("samples must be finite")
        if sample < -1.0 or sample > 1.0:
            raise ValueError("samples must be between -1.0 and 1.0")
        validated.append(float(sample))
    return validated


def _wavegen_channel_limits(channel: int, limits: WavegenLimits) -> WavegenChannelLimits:
    return limits.channel_limits[str(channel)]


def _validate_range(name: str, value: float, minimum: float, maximum: float) -> None:
    if value < minimum or value > maximum:
        raise ValueError(f"{name} must be between {minimum} and {maximum}")


def _wavegen_status_payload(
    status: WavegenStatus,
    selected_device: DeviceInfo,
) -> dict[str, object]:
    config = (
        {key: value for key, value in asdict(status.config).items() if value is not None}
        if status.config
        else None
    )
    return {
        "channel": status.channel,
        "state": status.state,
        "running": status.running,
        "config": config,
        "device": asdict(selected_device),
    }


def _synchronized_wavegen_payload(
    statuses: list[WavegenStatus],
    master_channel: int,
    selected_device: DeviceInfo,
) -> dict[str, object]:
    slave_channels = [status.channel for status in statuses if status.channel != master_channel]
    status_payloads = []
    for status in statuses:
        config = (
            {key: value for key, value in asdict(status.config).items() if value is not None}
            if status.config
            else None
        )
        status_payloads.append(
            {
                "channel": status.channel,
                "state": status.state,
                "running": status.running,
                "config": config,
            }
        )
    return {
        "synchronized": True,
        "master_channel": master_channel,
        "slave_channels": slave_channels,
        "statuses": status_payloads,
        "device": asdict(selected_device),
    }
