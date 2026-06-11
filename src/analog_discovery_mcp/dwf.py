from __future__ import annotations

import sys
import time
from ctypes import (
    CDLL,
    byref,
    c_byte,
    c_double,
    c_int,
    c_uint,
    create_string_buffer,
)
from typing import Any, cast

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

ACQMODE_SINGLE = 0
DWF_STATE_DONE = 2
DWF_STATE_RUNNING = 3
TRIGSRC_NONE = 0
TRIGSRC_DETECTOR_ANALOG_IN = 2
TRIGTYPE_EDGE = 0
TRIGGER_SLOPE_RISE = 0
TRIGGER_SLOPE_FALL = 1
ANALOG_OUT_NODE_CARRIER = 0
FUNC_DC = 0
FUNC_SINE = 1
FUNC_SQUARE = 2
FUNC_TRIANGLE = 3
FUNC_CUSTOM = 30
WAVEGEN_FUNCTIONS = {
    "sine": FUNC_SINE,
    "square": FUNC_SQUARE,
    "triangle": FUNC_TRIANGLE,
    "dc": FUNC_DC,
    "custom": FUNC_CUSTOM,
}
WAVEGEN_FUNCTION_NAMES = {value: key for key, value in WAVEGEN_FUNCTIONS.items()}
DEFAULT_CAPTURE_SAMPLE_RATE_HZ = 1000.0
DEFAULT_CAPTURE_SAMPLE_COUNT = 1000
DEFAULT_WAVEGEN_FREQUENCY_HZ = 1000.0
DEFAULT_WAVEGEN_AMPLITUDE_V = 1.0
DEFAULT_WAVEGEN_OFFSET_V = 0.0
DEFAULT_WAVEGEN_DUTY_CYCLE_PERCENT = 50.0
MAX_TOTAL_RETURNED_SAMPLES = 65_536
ANALOG_CAPTURE_TIMEOUT_SECONDS = 5.0
ANALOG_CAPTURE_POLL_INTERVAL_SECONDS = 0.001


class DwfError(RuntimeError):
    """Base error for WaveForms SDK access."""


class DwfUnavailableError(DwfError):
    """Raised when the WaveForms SDK dynamic library cannot be loaded."""


class DeviceOpenError(DwfError):
    """Raised when a selected WaveForms device cannot be opened."""


def default_library_path() -> str:
    if sys.platform.startswith("win"):
        return "dwf"
    if sys.platform.startswith("darwin"):
        return "/Library/Frameworks/dwf.framework/dwf"
    return "libdwf.so"


class CtypesDwfAdapter:
    """Small ctypes wrapper around the Digilent WaveForms SDK functions used by v1."""

    def __init__(self, library_path: str | None = None) -> None:
        path = library_path or default_library_path()
        try:
            self._dwf = cast(Any, CDLL(path))
        except OSError as exc:
            raise DwfUnavailableError(f"Unable to load WaveForms SDK library: {path}") from exc

    def get_version(self) -> str:
        version = create_string_buffer(32)
        self._require_ok(self._dwf.FDwfGetVersion(version))
        return _decode_buffer(version)

    def list_devices(self) -> list[DeviceInfo]:
        count = c_int()
        self._require_ok(self._dwf.FDwfEnum(c_int(0), byref(count)))

        devices: list[DeviceInfo] = []
        for index in range(count.value):
            name = create_string_buffer(64)
            serial = create_string_buffer(64)
            available = c_byte()

            self._require_ok(self._dwf.FDwfEnumDeviceName(c_int(index), name))
            self._require_ok(self._dwf.FDwfEnumSN(c_int(index), serial))

            available_ok = self._dwf.FDwfEnumDeviceIsOpened(c_int(index), byref(available))
            is_available = bool(available_ok and not available.value)

            devices.append(
                DeviceInfo(
                    index=index,
                    name=_decode_buffer(name),
                    serial_number=_decode_buffer(serial),
                    available=is_available,
                )
            )

        return devices

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        handle = c_int()
        self._require_ok(self._dwf.FDwfDeviceOpen(c_int(device_index), byref(handle)))
        if handle.value == 0:
            raise DeviceOpenError(self._last_error_message("Unable to open WaveForms device"))

        try:
            self._require_ok(self._dwf.FDwfDeviceAutoConfigureSet(handle, c_int(0)))
            self._require_ok(
                self._dwf.FDwfAnalogInChannelEnableSet(handle, c_int(channel_index), c_int(1))
            )
            self._require_ok(self._dwf.FDwfAnalogInConfigure(handle, c_int(0), c_int(0)))
            self._require_ok(self._dwf.FDwfAnalogInStatus(handle, c_int(0), None))

            voltage = c_double()
            self._require_ok(
                self._dwf.FDwfAnalogInStatusSample(handle, c_int(channel_index), byref(voltage))
            )
            return float(voltage.value)
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def get_analog_capture_limits(self, device_index: int) -> AnalogCaptureLimits:
        handle = self._open_device(device_index)

        try:
            channel_count = c_int()
            frequency_min = c_double()
            frequency_max = c_double()
            buffer_min = c_int()
            buffer_max = c_int()

            self._require_ok(self._dwf.FDwfAnalogInChannelCount(handle, byref(channel_count)))
            self._require_ok(
                self._dwf.FDwfAnalogInFrequencyInfo(
                    handle,
                    byref(frequency_min),
                    byref(frequency_max),
                )
            )
            self._require_ok(
                self._dwf.FDwfAnalogInBufferSizeInfo(
                    handle,
                    byref(buffer_min),
                    byref(buffer_max),
                )
            )

            supported_channel_count = max(0, channel_count.value)
            max_sample_count = max(1, buffer_max.value)
            max_total_samples = min(
                max_sample_count * max(1, supported_channel_count),
                MAX_TOTAL_RETURNED_SAMPLES,
            )
            default_sample_count = min(DEFAULT_CAPTURE_SAMPLE_COUNT, max_sample_count)

            return AnalogCaptureLimits(
                supported_channels=list(range(1, supported_channel_count + 1)),
                default_sample_rate_hz=_clamp(
                    DEFAULT_CAPTURE_SAMPLE_RATE_HZ,
                    frequency_min.value,
                    frequency_max.value,
                ),
                default_sample_count=default_sample_count,
                max_sample_count_per_channel=max_sample_count,
                max_total_returned_samples=max_total_samples,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def capture_analog_waveform(
        self,
        device_index: int,
        channel_indices: list[int],
        sample_rate_hz: float,
        sample_count: int,
        trigger_config: AnalogTriggerConfig | None = None,
    ) -> AnalogCapture:
        handle = self._open_device(device_index)

        try:
            self._require_ok(self._dwf.FDwfDeviceAutoConfigureSet(handle, c_int(0)))
            self._require_ok(self._dwf.FDwfAnalogInReset(handle))

            for channel_index in channel_indices:
                self._require_ok(
                    self._dwf.FDwfAnalogInChannelEnableSet(
                        handle,
                        c_int(channel_index),
                        c_int(1),
                    )
                )

            self._require_ok(
                self._dwf.FDwfAnalogInAcquisitionModeSet(handle, c_int(ACQMODE_SINGLE))
            )
            self._require_ok(self._dwf.FDwfAnalogInFrequencySet(handle, c_double(sample_rate_hz)))
            self._require_ok(self._dwf.FDwfAnalogInBufferSizeSet(handle, c_int(sample_count)))
            self._configure_analog_trigger(handle, trigger_config)
            self._require_ok(self._dwf.FDwfAnalogInConfigure(handle, c_int(1), c_int(1)))
            self._wait_for_analog_capture(handle, sample_count, sample_rate_hz, trigger_config)

            actual_sample_rate = c_double()
            self._require_ok(self._dwf.FDwfAnalogInFrequencyGet(handle, byref(actual_sample_rate)))
            metadata = self._read_analog_capture_metadata(handle, trigger_config)

            samples: dict[str, list[float]] = {}
            for channel_index in channel_indices:
                sample_buffer = (c_double * sample_count)()
                self._require_ok(
                    self._dwf.FDwfAnalogInStatusData(
                        handle,
                        c_int(channel_index),
                        sample_buffer,
                        c_int(sample_count),
                    )
                )
                samples[str(channel_index + 1)] = [float(sample) for sample in sample_buffer]

            return AnalogCapture(
                sample_rate_hz=float(actual_sample_rate.value),
                sample_count=sample_count,
                channels=[channel_index + 1 for channel_index in channel_indices],
                samples=samples,
                triggered=metadata["triggered"],
                auto_triggered=metadata["auto_triggered"],
                valid_sample_count=metadata["valid_sample_count"],
                lost_sample_count=metadata["lost_sample_count"],
                corrupt_sample_count=metadata["corrupt_sample_count"],
                status_time=metadata["status_time"],
                trigger=trigger_config,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def get_analog_input_status(self, device_index: int) -> AnalogInputStatus:
        handle = self._open_device(device_index)

        try:
            channel_count = c_int()
            frequency_min = c_double()
            frequency_max = c_double()
            current_frequency = c_double()
            buffer_min = c_int()
            buffer_max = c_int()
            current_buffer = c_int()
            state = c_byte()

            self._require_ok(self._dwf.FDwfAnalogInChannelCount(handle, byref(channel_count)))
            self._require_ok(
                self._dwf.FDwfAnalogInFrequencyInfo(
                    handle,
                    byref(frequency_min),
                    byref(frequency_max),
                )
            )
            self._require_ok(self._dwf.FDwfAnalogInFrequencyGet(handle, byref(current_frequency)))
            self._require_ok(
                self._dwf.FDwfAnalogInBufferSizeInfo(
                    handle,
                    byref(buffer_min),
                    byref(buffer_max),
                )
            )
            self._require_ok(self._dwf.FDwfAnalogInBufferSizeGet(handle, byref(current_buffer)))
            self._require_ok(self._dwf.FDwfAnalogInStatus(handle, c_int(0), byref(state)))

            channel_ranges: dict[str, float] = {}
            channel_offsets: dict[str, float] = {}
            for channel_index in range(max(0, channel_count.value)):
                channel_key = str(channel_index + 1)
                channel_range = c_double()
                channel_offset = c_double()
                self._require_ok(
                    self._dwf.FDwfAnalogInChannelRangeGet(
                        handle,
                        c_int(channel_index),
                        byref(channel_range),
                    )
                )
                self._require_ok(
                    self._dwf.FDwfAnalogInChannelOffsetGet(
                        handle,
                        c_int(channel_index),
                        byref(channel_offset),
                    )
                )
                channel_ranges[channel_key] = float(channel_range.value)
                channel_offsets[channel_key] = float(channel_offset.value)

            return AnalogInputStatus(
                channel_count=max(0, channel_count.value),
                frequency_min_hz=float(frequency_min.value),
                frequency_max_hz=float(frequency_max.value),
                current_frequency_hz=float(current_frequency.value),
                buffer_size_min=buffer_min.value,
                buffer_size_max=buffer_max.value,
                current_buffer_size=current_buffer.value,
                channel_ranges=channel_ranges,
                channel_offsets=channel_offsets,
                state=int(state.value),
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def get_wavegen_limits(self, device_index: int) -> WavegenLimits:
        handle = self._open_device(device_index)

        try:
            channel_count = c_int()
            self._require_ok(self._dwf.FDwfAnalogOutCount(handle, byref(channel_count)))

            supported_channels: list[int] = []
            supported_waveform_values: set[int] | None = None
            channel_limits: dict[str, WavegenChannelLimits] = {}

            for channel_index in range(max(0, channel_count.value)):
                node_options = c_int()
                self._require_ok(
                    self._dwf.FDwfAnalogOutNodeInfo(
                        handle,
                        c_int(channel_index),
                        byref(node_options),
                    )
                )
                if not _bit_is_set(node_options.value, ANALOG_OUT_NODE_CARRIER):
                    continue

                function_options = c_int()
                frequency_min = c_double()
                frequency_max = c_double()
                amplitude_min = c_double()
                amplitude_max = c_double()
                offset_min = c_double()
                offset_max = c_double()
                duty_min = c_double()
                duty_max = c_double()
                custom_sample_count_min: int | None = None
                custom_sample_count_max: int | None = None

                self._require_ok(
                    self._dwf.FDwfAnalogOutNodeFunctionInfo(
                        handle,
                        c_int(channel_index),
                        c_int(ANALOG_OUT_NODE_CARRIER),
                        byref(function_options),
                    )
                )
                self._require_ok(
                    self._dwf.FDwfAnalogOutNodeFrequencyInfo(
                        handle,
                        c_int(channel_index),
                        c_int(ANALOG_OUT_NODE_CARRIER),
                        byref(frequency_min),
                        byref(frequency_max),
                    )
                )
                self._require_ok(
                    self._dwf.FDwfAnalogOutNodeAmplitudeInfo(
                        handle,
                        c_int(channel_index),
                        c_int(ANALOG_OUT_NODE_CARRIER),
                        byref(amplitude_min),
                        byref(amplitude_max),
                    )
                )
                self._require_ok(
                    self._dwf.FDwfAnalogOutNodeOffsetInfo(
                        handle,
                        c_int(channel_index),
                        c_int(ANALOG_OUT_NODE_CARRIER),
                        byref(offset_min),
                        byref(offset_max),
                    )
                )
                self._require_ok(
                    self._dwf.FDwfAnalogOutNodeSymmetryInfo(
                        handle,
                        c_int(channel_index),
                        c_int(ANALOG_OUT_NODE_CARRIER),
                        byref(duty_min),
                        byref(duty_max),
                    )
                )

                supported_channels.append(channel_index + 1)
                function_values = {
                    value
                    for value in WAVEGEN_FUNCTIONS.values()
                    if _bit_is_set(function_options.value, value)
                }
                if FUNC_CUSTOM in function_values:
                    data_min = c_int()
                    data_max = c_int()
                    self._require_ok(
                        self._dwf.FDwfAnalogOutNodeDataInfo(
                            handle,
                            c_int(channel_index),
                            c_int(ANALOG_OUT_NODE_CARRIER),
                            byref(data_min),
                            byref(data_max),
                        )
                    )
                    custom_sample_count_min = max(1, data_min.value)
                    custom_sample_count_max = max(custom_sample_count_min, data_max.value)
                supported_waveform_values = (
                    function_values
                    if supported_waveform_values is None
                    else supported_waveform_values & function_values
                )
                channel_limits[str(channel_index + 1)] = WavegenChannelLimits(
                    frequency_min_hz=float(frequency_min.value),
                    frequency_max_hz=float(frequency_max.value),
                    amplitude_min_v=float(amplitude_min.value),
                    amplitude_max_v=float(amplitude_max.value),
                    offset_min_v=float(offset_min.value),
                    offset_max_v=float(offset_max.value),
                    duty_cycle_min_percent=float(duty_min.value),
                    duty_cycle_max_percent=float(duty_max.value),
                    custom_sample_count_min=custom_sample_count_min,
                    custom_sample_count_max=custom_sample_count_max,
                )

            supported_waveforms = [
                name
                for name, value in WAVEGEN_FUNCTIONS.items()
                if supported_waveform_values is not None and value in supported_waveform_values
            ]
            if not supported_channels or not supported_waveforms:
                raise DwfError("selected device does not report supported Wavegen output")
            default_waveform = "sine" if "sine" in supported_waveforms else supported_waveforms[0]
            return WavegenLimits(
                supported_channels=supported_channels,
                supported_waveforms=supported_waveforms,
                default_waveform=default_waveform,
                default_frequency_hz=DEFAULT_WAVEGEN_FREQUENCY_HZ,
                default_amplitude_v=DEFAULT_WAVEGEN_AMPLITUDE_V,
                default_offset_v=DEFAULT_WAVEGEN_OFFSET_V,
                default_duty_cycle_percent=DEFAULT_WAVEGEN_DUTY_CYCLE_PERCENT,
                channel_limits=channel_limits,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def get_digital_io_limits(self, device_index: int) -> DigitalIOLimits:
        handle = self._open_device(device_index)

        try:
            input_mask = c_uint()
            output_enable_mask = c_uint()
            output_mask = c_uint()

            self._require_ok(self._dwf.FDwfDigitalIOInputInfo(handle, byref(input_mask)))
            self._require_ok(
                self._dwf.FDwfDigitalIOOutputEnableInfo(
                    handle,
                    byref(output_enable_mask),
                )
            )
            self._require_ok(self._dwf.FDwfDigitalIOOutputInfo(handle, byref(output_mask)))

            supported_output_mask = output_enable_mask.value & output_mask.value
            return DigitalIOLimits(
                supported_input_pins=_mask_to_pins(input_mask.value),
                supported_output_pins=_mask_to_pins(supported_output_mask),
                input_mask=input_mask.value,
                output_enable_mask=supported_output_mask,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def read_digital_inputs(self, device_index: int, pins: list[int]) -> DigitalInputRead:
        handle = self._open_device(device_index)

        try:
            input_mask = self._read_digital_input_mask(handle)
            return DigitalInputRead(
                pins=pins,
                values=_digital_values(input_mask, pins),
                input_mask=input_mask,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def write_digital_outputs(
        self,
        device_index: int,
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
    ) -> DigitalOutputStatus:
        handle = self._open_device(device_index)

        try:
            selected_mask = _pins_to_mask(pins)
            values_mask = _pin_values_to_mask(pins, values)
            current_enable_mask = c_uint()
            current_output_mask = c_uint()
            self._require_ok(
                self._dwf.FDwfDigitalIOOutputEnableGet(handle, byref(current_enable_mask))
            )
            self._require_ok(self._dwf.FDwfDigitalIOOutputGet(handle, byref(current_output_mask)))

            if preserve_existing:
                output_enable_mask = current_enable_mask.value | selected_mask
                output_mask = (current_output_mask.value & ~selected_mask) | values_mask
            else:
                output_enable_mask = selected_mask
                output_mask = values_mask

            self._require_ok(
                self._dwf.FDwfDigitalIOOutputEnableSet(handle, c_uint(output_enable_mask))
            )
            self._require_ok(self._dwf.FDwfDigitalIOOutputSet(handle, c_uint(output_mask)))
            self._require_ok(self._dwf.FDwfDigitalIOConfigure(handle))

            return DigitalOutputStatus(
                pins=pins,
                values=_digital_values(output_mask, pins),
                output_enable_mask=output_enable_mask,
                output_mask=output_mask,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def start_wavegen(self, device_index: int, config: WavegenConfig) -> WavegenStatus:
        handle = self._open_device(device_index)

        try:
            channel_index = config.channel - 1
            self._require_ok(self._dwf.FDwfDeviceAutoConfigureSet(handle, c_int(0)))
            self._require_ok(self._dwf.FDwfAnalogOutReset(handle, c_int(channel_index)))
            self._require_ok(
                self._dwf.FDwfAnalogOutNodeEnableSet(
                    handle,
                    c_int(channel_index),
                    c_int(ANALOG_OUT_NODE_CARRIER),
                    c_int(1),
                )
            )
            self._write_wavegen_config(handle, channel_index, config)
            self._require_ok(
                self._dwf.FDwfAnalogOutConfigure(handle, c_int(channel_index), c_int(1))
            )
            return WavegenStatus(
                channel=config.channel,
                state=DWF_STATE_RUNNING,
                running=True,
                config=config,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def stop_wavegen(self, device_index: int, channel: int) -> WavegenStatus:
        handle = self._open_device(device_index)

        try:
            channel_index = channel - 1
            config = self._read_wavegen_config(handle, channel_index, channel)
            self._require_ok(
                self._dwf.FDwfAnalogOutConfigure(handle, c_int(channel_index), c_int(0))
            )
            status = c_byte()
            self._require_ok(
                self._dwf.FDwfAnalogOutStatus(handle, c_int(channel_index), byref(status))
            )
            return WavegenStatus(
                channel=channel,
                state=int(status.value),
                running=False,
                config=config,
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def get_wavegen_status(self, device_index: int, channel: int) -> WavegenStatus:
        handle = self._open_device(device_index)

        try:
            channel_index = channel - 1
            status = c_byte()
            self._require_ok(
                self._dwf.FDwfAnalogOutStatus(handle, c_int(channel_index), byref(status))
            )
            return WavegenStatus(
                channel=channel,
                state=int(status.value),
                running=status.value == DWF_STATE_RUNNING,
                config=self._read_wavegen_config(handle, channel_index, channel),
            )
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def _open_device(self, device_index: int) -> c_int:
        handle = c_int()
        self._require_ok(self._dwf.FDwfDeviceOpen(c_int(device_index), byref(handle)))
        if handle.value == 0:
            raise DeviceOpenError(self._last_error_message("Unable to open WaveForms device"))
        return handle

    def _write_wavegen_config(
        self,
        handle: c_int,
        channel_index: int,
        config: WavegenConfig,
    ) -> None:
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeFunctionSet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                c_byte(WAVEGEN_FUNCTIONS[config.waveform]),
            )
        )
        if config.waveform == "custom":
            if config.samples is None:
                raise DwfError("custom Wavegen config is missing samples")
            sample_buffer = (c_double * len(config.samples))(*config.samples)
            self._require_ok(
                self._dwf.FDwfAnalogOutNodeDataSet(
                    handle,
                    c_int(channel_index),
                    c_int(ANALOG_OUT_NODE_CARRIER),
                    sample_buffer,
                    c_int(len(config.samples)),
                )
            )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeFrequencySet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                c_double(config.frequency_hz),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeAmplitudeSet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                c_double(config.amplitude_v),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeOffsetSet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                c_double(config.offset_v),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeSymmetrySet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                c_double(config.duty_cycle_percent),
            )
        )

    def _read_wavegen_config(
        self,
        handle: c_int,
        channel_index: int,
        channel: int,
    ) -> WavegenConfig | None:
        function = c_byte()
        frequency = c_double()
        amplitude = c_double()
        offset = c_double()
        duty_cycle = c_double()

        self._require_ok(
            self._dwf.FDwfAnalogOutNodeFunctionGet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                byref(function),
            )
        )
        waveform = WAVEGEN_FUNCTION_NAMES.get(function.value)
        if waveform is None:
            return None

        self._require_ok(
            self._dwf.FDwfAnalogOutNodeFrequencyGet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                byref(frequency),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeAmplitudeGet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                byref(amplitude),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeOffsetGet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                byref(offset),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogOutNodeSymmetryGet(
                handle,
                c_int(channel_index),
                c_int(ANALOG_OUT_NODE_CARRIER),
                byref(duty_cycle),
            )
        )

        return WavegenConfig(
            channel=channel,
            waveform=waveform,
            frequency_hz=float(frequency.value),
            amplitude_v=float(amplitude.value),
            offset_v=float(offset.value),
            duty_cycle_percent=float(duty_cycle.value),
        )

    def _configure_analog_trigger(
        self,
        handle: c_int,
        trigger_config: AnalogTriggerConfig | None,
    ) -> None:
        if trigger_config is None:
            self._require_ok(self._dwf.FDwfAnalogInTriggerSourceSet(handle, c_byte(TRIGSRC_NONE)))
            return

        slope = TRIGGER_SLOPE_RISE if trigger_config.edge == "rising" else TRIGGER_SLOPE_FALL
        self._require_ok(
            self._dwf.FDwfAnalogInTriggerSourceSet(handle, c_byte(TRIGSRC_DETECTOR_ANALOG_IN))
        )
        self._require_ok(self._dwf.FDwfAnalogInTriggerTypeSet(handle, c_int(TRIGTYPE_EDGE)))
        self._require_ok(
            self._dwf.FDwfAnalogInTriggerChannelSet(handle, c_int(trigger_config.channel - 1))
        )
        self._require_ok(
            self._dwf.FDwfAnalogInTriggerLevelSet(handle, c_double(trigger_config.level_v))
        )
        self._require_ok(
            self._dwf.FDwfAnalogInTriggerHysteresisSet(
                handle,
                c_double(trigger_config.hysteresis_v),
            )
        )
        self._require_ok(self._dwf.FDwfAnalogInTriggerConditionSet(handle, c_int(slope)))
        self._require_ok(
            self._dwf.FDwfAnalogInTriggerAutoTimeoutSet(
                handle,
                c_double(trigger_config.auto_timeout_seconds),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogInTriggerPositionSet(
                handle,
                c_double(trigger_config.position_seconds),
            )
        )

    def _wait_for_analog_capture(
        self,
        handle: c_int,
        sample_count: int,
        sample_rate_hz: float,
        trigger_config: AnalogTriggerConfig | None,
    ) -> None:
        capture_duration = sample_count / sample_rate_hz
        trigger_wait = 0.0 if trigger_config is None else trigger_config.auto_timeout_seconds
        if hasattr(self, "_capture_timeout_seconds"):
            timeout_seconds = cast(float, self._capture_timeout_seconds)
        else:
            timeout_seconds = max(
                ANALOG_CAPTURE_TIMEOUT_SECONDS,
                trigger_wait + capture_duration + 1.0,
            )
        deadline = time.monotonic() + timeout_seconds
        status = c_byte()

        while True:
            self._require_ok(self._dwf.FDwfAnalogInStatus(handle, c_int(1), byref(status)))
            if status.value == DWF_STATE_DONE:
                return
            if time.monotonic() >= deadline:
                raise DwfError("analog waveform capture timed out")
            time.sleep(ANALOG_CAPTURE_POLL_INTERVAL_SECONDS)

    def _read_analog_capture_metadata(
        self,
        handle: c_int,
        trigger_config: AnalogTriggerConfig | None,
    ) -> dict[str, Any]:
        valid_samples = c_int()
        auto_triggered = c_int()
        data_available = c_int()
        lost_samples = c_int()
        corrupt_samples = c_int()
        seconds_utc = c_uint()
        tick = c_uint()
        ticks_per_second = c_uint()

        self._require_ok(self._dwf.FDwfAnalogInStatusSamplesValid(handle, byref(valid_samples)))
        self._require_ok(self._dwf.FDwfAnalogInStatusAutoTriggered(handle, byref(auto_triggered)))
        self._require_ok(
            self._dwf.FDwfAnalogInStatusRecord(
                handle,
                byref(data_available),
                byref(lost_samples),
                byref(corrupt_samples),
            )
        )
        self._require_ok(
            self._dwf.FDwfAnalogInStatusTime(
                handle,
                byref(seconds_utc),
                byref(tick),
                byref(ticks_per_second),
            )
        )

        auto_triggered_value = bool(auto_triggered.value)
        return {
            "triggered": trigger_config is not None and not auto_triggered_value,
            "auto_triggered": auto_triggered_value if trigger_config is not None else None,
            "valid_sample_count": valid_samples.value,
            "lost_sample_count": lost_samples.value,
            "corrupt_sample_count": corrupt_samples.value,
            "status_time": AnalogStatusTime(
                seconds_utc=seconds_utc.value,
                tick=tick.value,
                ticks_per_second=ticks_per_second.value,
            ),
        }

    def _read_digital_input_mask(self, handle: c_int) -> int:
        input_mask = c_uint()
        self._require_ok(self._dwf.FDwfDigitalIOStatus(handle))
        self._require_ok(self._dwf.FDwfDigitalIOInputStatus(handle, byref(input_mask)))
        return input_mask.value

    def _require_ok(self, result: int) -> None:
        if not result:
            raise DwfError(self._last_error_message("WaveForms SDK call failed"))

    def _last_error_message(self, fallback: str) -> str:
        message = create_string_buffer(512)
        get_last_error = getattr(self._dwf, "FDwfGetLastErrorMsg", None)
        if not callable(get_last_error):
            return fallback
        get_last_error(message)
        decoded = _decode_buffer(message)
        return decoded or fallback


def _decode_buffer(buffer: object) -> str:
    value = getattr(buffer, "value", b"")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


def _clamp(value: float, minimum: float, maximum: float) -> float:
    return min(max(value, minimum), maximum)


def _bit_is_set(value: int, bit_index: int) -> bool:
    return bool(value & (1 << bit_index))


def _mask_to_pins(mask: int) -> list[int]:
    return [pin for pin in range(32) if mask & (1 << pin)]


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


class LazyDwfAdapter:
    """Delay WaveForms SDK loading until a tool actually needs hardware access."""

    def __init__(self, library_path: str | None = None) -> None:
        self._library_path = library_path
        self._adapter: CtypesDwfAdapter | None = None

    def get_version(self) -> str:
        return self._get_adapter().get_version()

    def list_devices(self) -> list[DeviceInfo]:
        return self._get_adapter().list_devices()

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        return self._get_adapter().read_analog_voltage(device_index, channel_index)

    def get_analog_capture_limits(self, device_index: int) -> AnalogCaptureLimits:
        return self._get_adapter().get_analog_capture_limits(device_index)

    def capture_analog_waveform(
        self,
        device_index: int,
        channel_indices: list[int],
        sample_rate_hz: float,
        sample_count: int,
        trigger_config: AnalogTriggerConfig | None = None,
    ) -> AnalogCapture:
        return self._get_adapter().capture_analog_waveform(
            device_index,
            channel_indices,
            sample_rate_hz,
            sample_count,
            trigger_config,
        )

    def get_analog_input_status(self, device_index: int) -> AnalogInputStatus:
        return self._get_adapter().get_analog_input_status(device_index)

    def get_digital_io_limits(self, device_index: int) -> DigitalIOLimits:
        return self._get_adapter().get_digital_io_limits(device_index)

    def read_digital_inputs(self, device_index: int, pins: list[int]) -> DigitalInputRead:
        return self._get_adapter().read_digital_inputs(device_index, pins)

    def write_digital_outputs(
        self,
        device_index: int,
        pins: list[int],
        values: list[bool],
        preserve_existing: bool = True,
    ) -> DigitalOutputStatus:
        return self._get_adapter().write_digital_outputs(
            device_index,
            pins,
            values,
            preserve_existing,
        )

    def get_wavegen_limits(self, device_index: int) -> WavegenLimits:
        return self._get_adapter().get_wavegen_limits(device_index)

    def start_wavegen(self, device_index: int, config: WavegenConfig) -> WavegenStatus:
        return self._get_adapter().start_wavegen(device_index, config)

    def stop_wavegen(self, device_index: int, channel: int) -> WavegenStatus:
        return self._get_adapter().stop_wavegen(device_index, channel)

    def get_wavegen_status(self, device_index: int, channel: int) -> WavegenStatus:
        return self._get_adapter().get_wavegen_status(device_index, channel)

    def _get_adapter(self) -> CtypesDwfAdapter:
        if self._adapter is None:
            self._adapter = CtypesDwfAdapter(self._library_path)
        return self._adapter
