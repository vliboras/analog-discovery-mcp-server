from __future__ import annotations

from ctypes import c_byte, c_double, c_int, c_uint
from typing import Any, cast

import pytest

from analog_discovery_mcp.dwf import CtypesDwfAdapter, DwfError
from analog_discovery_mcp.models import AnalogTriggerConfig, WavegenConfig


class FakeWaveFormsSdk:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.status_values = [2]
        self.fail_on: str | None = None
        self.last_error = "fake sdk failure"
        self.digital_input_info_mask = 0xFFFF
        self.digital_output_enable_info_mask = 0xFFFF
        self.digital_output_info_mask = 0xFFFF
        self.digital_input_status_mask = 0
        self.digital_output_enable_mask = 0
        self.digital_output_mask = 0

    def FDwfDeviceOpen(self, device_index: object, handle: object) -> int:
        self._record("FDwfDeviceOpen", device_index)
        self._set_value(handle, 7)
        return self._result("FDwfDeviceOpen")

    def FDwfDeviceClose(self, handle: object) -> int:
        self._record("FDwfDeviceClose", handle)
        return 1

    def FDwfAnalogInChannelCount(self, handle: object, channel_count: object) -> int:
        self._record("FDwfAnalogInChannelCount", handle)
        self._set_value(channel_count, 2)
        return self._result("FDwfAnalogInChannelCount")

    def FDwfAnalogInFrequencyInfo(
        self,
        handle: object,
        frequency_min: object,
        frequency_max: object,
    ) -> int:
        self._record("FDwfAnalogInFrequencyInfo", handle)
        self._set_value(frequency_min, 1.0)
        self._set_value(frequency_max, 100_000_000.0)
        return self._result("FDwfAnalogInFrequencyInfo")

    def FDwfAnalogInBufferSizeInfo(
        self,
        handle: object,
        buffer_min: object,
        buffer_max: object,
    ) -> int:
        self._record("FDwfAnalogInBufferSizeInfo", handle)
        self._set_value(buffer_min, 1)
        self._set_value(buffer_max, 32_768)
        return self._result("FDwfAnalogInBufferSizeInfo")

    def FDwfDeviceAutoConfigureSet(self, handle: object, enabled: object) -> int:
        self._record("FDwfDeviceAutoConfigureSet", handle, enabled)
        return self._result("FDwfDeviceAutoConfigureSet")

    def FDwfAnalogInReset(self, handle: object) -> int:
        self._record("FDwfAnalogInReset", handle)
        return self._result("FDwfAnalogInReset")

    def FDwfAnalogInChannelEnableSet(
        self,
        handle: object,
        channel_index: object,
        enabled: object,
    ) -> int:
        self._record("FDwfAnalogInChannelEnableSet", handle, channel_index, enabled)
        return self._result("FDwfAnalogInChannelEnableSet")

    def FDwfAnalogInAcquisitionModeSet(self, handle: object, acquisition_mode: object) -> int:
        self._record("FDwfAnalogInAcquisitionModeSet", handle, acquisition_mode)
        return self._result("FDwfAnalogInAcquisitionModeSet")

    def FDwfAnalogInFrequencySet(self, handle: object, sample_rate_hz: object) -> int:
        self._record("FDwfAnalogInFrequencySet", handle, sample_rate_hz)
        return self._result("FDwfAnalogInFrequencySet")

    def FDwfAnalogInBufferSizeSet(self, handle: object, sample_count: object) -> int:
        self._record("FDwfAnalogInBufferSizeSet", handle, sample_count)
        return self._result("FDwfAnalogInBufferSizeSet")

    def FDwfAnalogInConfigure(
        self,
        handle: object,
        reconfigure: object,
        start: object,
    ) -> int:
        self._record("FDwfAnalogInConfigure", handle, reconfigure, start)
        return self._result("FDwfAnalogInConfigure")

    def FDwfAnalogInStatus(self, handle: object, read_data: object, status: object) -> int:
        self._record("FDwfAnalogInStatus", handle, read_data)
        value = self.status_values.pop(0) if self.status_values else 2
        self._set_value(status, value)
        return self._result("FDwfAnalogInStatus")

    def FDwfAnalogInFrequencyGet(self, handle: object, sample_rate_hz: object) -> int:
        self._record("FDwfAnalogInFrequencyGet", handle)
        self._set_value(sample_rate_hz, 999.5)
        return self._result("FDwfAnalogInFrequencyGet")

    def FDwfAnalogInBufferSizeGet(self, handle: object, sample_count: object) -> int:
        self._record("FDwfAnalogInBufferSizeGet", handle)
        self._set_value(sample_count, 4096)
        return self._result("FDwfAnalogInBufferSizeGet")

    def FDwfAnalogInChannelRangeGet(
        self,
        handle: object,
        channel_index: object,
        channel_range: object,
    ) -> int:
        self._record("FDwfAnalogInChannelRangeGet", handle, channel_index)
        self._set_value(channel_range, 5.0)
        return self._result("FDwfAnalogInChannelRangeGet")

    def FDwfAnalogInChannelOffsetGet(
        self,
        handle: object,
        channel_index: object,
        channel_offset: object,
    ) -> int:
        self._record("FDwfAnalogInChannelOffsetGet", handle, channel_index)
        self._set_value(channel_offset, 0.0)
        return self._result("FDwfAnalogInChannelOffsetGet")

    def FDwfAnalogInTriggerSourceSet(self, handle: object, source: object) -> int:
        self._record("FDwfAnalogInTriggerSourceSet", handle, source)
        return self._result("FDwfAnalogInTriggerSourceSet")

    def FDwfAnalogInTriggerTypeSet(self, handle: object, trigger_type: object) -> int:
        self._record("FDwfAnalogInTriggerTypeSet", handle, trigger_type)
        return self._result("FDwfAnalogInTriggerTypeSet")

    def FDwfAnalogInTriggerChannelSet(self, handle: object, channel_index: object) -> int:
        self._record("FDwfAnalogInTriggerChannelSet", handle, channel_index)
        return self._result("FDwfAnalogInTriggerChannelSet")

    def FDwfAnalogInTriggerLevelSet(self, handle: object, level: object) -> int:
        self._record("FDwfAnalogInTriggerLevelSet", handle, level)
        return self._result("FDwfAnalogInTriggerLevelSet")

    def FDwfAnalogInTriggerHysteresisSet(self, handle: object, hysteresis: object) -> int:
        self._record("FDwfAnalogInTriggerHysteresisSet", handle, hysteresis)
        return self._result("FDwfAnalogInTriggerHysteresisSet")

    def FDwfAnalogInTriggerConditionSet(self, handle: object, condition: object) -> int:
        self._record("FDwfAnalogInTriggerConditionSet", handle, condition)
        return self._result("FDwfAnalogInTriggerConditionSet")

    def FDwfAnalogInTriggerAutoTimeoutSet(self, handle: object, timeout: object) -> int:
        self._record("FDwfAnalogInTriggerAutoTimeoutSet", handle, timeout)
        return self._result("FDwfAnalogInTriggerAutoTimeoutSet")

    def FDwfAnalogInTriggerPositionSet(self, handle: object, position: object) -> int:
        self._record("FDwfAnalogInTriggerPositionSet", handle, position)
        return self._result("FDwfAnalogInTriggerPositionSet")

    def FDwfAnalogInStatusSamplesValid(self, handle: object, sample_count: object) -> int:
        self._record("FDwfAnalogInStatusSamplesValid", handle)
        self._set_value(sample_count, 4)
        return self._result("FDwfAnalogInStatusSamplesValid")

    def FDwfAnalogInStatusAutoTriggered(self, handle: object, auto_triggered: object) -> int:
        self._record("FDwfAnalogInStatusAutoTriggered", handle)
        self._set_value(auto_triggered, 0)
        return self._result("FDwfAnalogInStatusAutoTriggered")

    def FDwfAnalogInStatusRecord(
        self,
        handle: object,
        data_available: object,
        data_lost: object,
        data_corrupt: object,
    ) -> int:
        self._record("FDwfAnalogInStatusRecord", handle)
        self._set_value(data_available, 4)
        self._set_value(data_lost, 0)
        self._set_value(data_corrupt, 0)
        return self._result("FDwfAnalogInStatusRecord")

    def FDwfAnalogInStatusTime(
        self,
        handle: object,
        seconds_utc: object,
        tick: object,
        ticks_per_second: object,
    ) -> int:
        self._record("FDwfAnalogInStatusTime", handle)
        self._set_value(seconds_utc, 123)
        self._set_value(tick, 456)
        self._set_value(ticks_per_second, 1_000_000)
        return self._result("FDwfAnalogInStatusTime")

    def FDwfAnalogInStatusData(
        self,
        handle: object,
        channel_index: object,
        sample_buffer: object,
        sample_count: object,
    ) -> int:
        channel = self._value(channel_index)
        count = self._value(sample_count)
        self._record("FDwfAnalogInStatusData", handle, channel_index, sample_count)
        for index in range(count):
            sample_buffer[index] = float(channel * 10 + index)  # type: ignore[index]
        return self._result("FDwfAnalogInStatusData")

    def FDwfAnalogOutCount(self, handle: object, channel_count: object) -> int:
        self._record("FDwfAnalogOutCount", handle)
        self._set_value(channel_count, 2)
        return self._result("FDwfAnalogOutCount")

    def FDwfAnalogOutMasterSet(
        self,
        handle: object,
        channel_index: object,
        master_index: object,
    ) -> int:
        self._record("FDwfAnalogOutMasterSet", handle, channel_index, master_index)
        return self._result("FDwfAnalogOutMasterSet")

    def FDwfAnalogOutMasterGet(
        self,
        handle: object,
        channel_index: object,
        master_index: object,
    ) -> int:
        self._record("FDwfAnalogOutMasterGet", handle, channel_index)
        self._set_value(master_index, 0)
        return self._result("FDwfAnalogOutMasterGet")

    def FDwfAnalogOutNodeInfo(
        self,
        handle: object,
        channel_index: object,
        node_options: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeInfo", handle, channel_index)
        self._set_value(node_options, 1)
        return self._result("FDwfAnalogOutNodeInfo")

    def FDwfAnalogOutNodeFunctionInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        function_options: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeFunctionInfo", handle, channel_index, node_index)
        self._set_value(function_options, 0b1111 | (1 << 30))
        return self._result("FDwfAnalogOutNodeFunctionInfo")

    def FDwfAnalogOutNodeDataInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        samples_min: object,
        samples_max: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeDataInfo", handle, channel_index, node_index)
        self._set_value(samples_min, 2)
        self._set_value(samples_max, 4096)
        return self._result("FDwfAnalogOutNodeDataInfo")

    def FDwfAnalogOutNodeFrequencyInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        frequency_min: object,
        frequency_max: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeFrequencyInfo", handle, channel_index, node_index)
        self._set_value(frequency_min, 0.1)
        self._set_value(frequency_max, 10_000_000.0)
        return self._result("FDwfAnalogOutNodeFrequencyInfo")

    def FDwfAnalogOutNodeAmplitudeInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        amplitude_min: object,
        amplitude_max: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeAmplitudeInfo", handle, channel_index, node_index)
        self._set_value(amplitude_min, 0.0)
        self._set_value(amplitude_max, 5.0)
        return self._result("FDwfAnalogOutNodeAmplitudeInfo")

    def FDwfAnalogOutNodeOffsetInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        offset_min: object,
        offset_max: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeOffsetInfo", handle, channel_index, node_index)
        self._set_value(offset_min, -5.0)
        self._set_value(offset_max, 5.0)
        return self._result("FDwfAnalogOutNodeOffsetInfo")

    def FDwfAnalogOutNodeSymmetryInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        duty_min: object,
        duty_max: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeSymmetryInfo", handle, channel_index, node_index)
        self._set_value(duty_min, 0.0)
        self._set_value(duty_max, 100.0)
        return self._result("FDwfAnalogOutNodeSymmetryInfo")

    def FDwfAnalogOutNodePhaseInfo(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        phase_min: object,
        phase_max: object,
    ) -> int:
        self._record("FDwfAnalogOutNodePhaseInfo", handle, channel_index, node_index)
        self._set_value(phase_min, -360.0)
        self._set_value(phase_max, 360.0)
        return self._result("FDwfAnalogOutNodePhaseInfo")

    def FDwfAnalogOutReset(self, handle: object, channel_index: object) -> int:
        self._record("FDwfAnalogOutReset", handle, channel_index)
        return self._result("FDwfAnalogOutReset")

    def FDwfAnalogOutNodeEnableSet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        enabled: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeEnableSet", handle, channel_index, node_index, enabled)
        return self._result("FDwfAnalogOutNodeEnableSet")

    def FDwfAnalogOutNodeFunctionSet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        function: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeFunctionSet", handle, channel_index, node_index, function)
        return self._result("FDwfAnalogOutNodeFunctionSet")

    def FDwfAnalogOutNodeFrequencySet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        frequency_hz: object,
    ) -> int:
        self._record(
            "FDwfAnalogOutNodeFrequencySet",
            handle,
            channel_index,
            node_index,
            frequency_hz,
        )
        return self._result("FDwfAnalogOutNodeFrequencySet")

    def FDwfAnalogOutNodeDataSet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        samples: object,
        sample_count: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeDataSet", handle, channel_index, node_index, sample_count)
        return self._result("FDwfAnalogOutNodeDataSet")

    def FDwfAnalogOutNodeAmplitudeSet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        amplitude_v: object,
    ) -> int:
        self._record(
            "FDwfAnalogOutNodeAmplitudeSet",
            handle,
            channel_index,
            node_index,
            amplitude_v,
        )
        return self._result("FDwfAnalogOutNodeAmplitudeSet")

    def FDwfAnalogOutNodeOffsetSet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        offset_v: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeOffsetSet", handle, channel_index, node_index, offset_v)
        return self._result("FDwfAnalogOutNodeOffsetSet")

    def FDwfAnalogOutNodeSymmetrySet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        duty_cycle: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeSymmetrySet", handle, channel_index, node_index, duty_cycle)
        return self._result("FDwfAnalogOutNodeSymmetrySet")

    def FDwfAnalogOutNodePhaseSet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        phase_degrees: object,
    ) -> int:
        self._record("FDwfAnalogOutNodePhaseSet", handle, channel_index, node_index, phase_degrees)
        return self._result("FDwfAnalogOutNodePhaseSet")

    def FDwfAnalogOutConfigure(self, handle: object, channel_index: object, start: object) -> int:
        self._record("FDwfAnalogOutConfigure", handle, channel_index, start)
        return self._result("FDwfAnalogOutConfigure")

    def FDwfAnalogOutStatus(self, handle: object, channel_index: object, status: object) -> int:
        self._record("FDwfAnalogOutStatus", handle, channel_index)
        self._set_value(status, 3)
        return self._result("FDwfAnalogOutStatus")

    def FDwfDigitalIOInputInfo(self, handle: object, input_mask: object) -> int:
        self._record("FDwfDigitalIOInputInfo", handle)
        self._set_value(input_mask, self.digital_input_info_mask)
        return self._result("FDwfDigitalIOInputInfo")

    def FDwfDigitalIOOutputEnableInfo(self, handle: object, output_enable_mask: object) -> int:
        self._record("FDwfDigitalIOOutputEnableInfo", handle)
        self._set_value(output_enable_mask, self.digital_output_enable_info_mask)
        return self._result("FDwfDigitalIOOutputEnableInfo")

    def FDwfDigitalIOOutputInfo(self, handle: object, output_mask: object) -> int:
        self._record("FDwfDigitalIOOutputInfo", handle)
        self._set_value(output_mask, self.digital_output_info_mask)
        return self._result("FDwfDigitalIOOutputInfo")

    def FDwfDigitalIOStatus(self, handle: object) -> int:
        self._record("FDwfDigitalIOStatus", handle)
        return self._result("FDwfDigitalIOStatus")

    def FDwfDigitalIOInputStatus(self, handle: object, input_mask: object) -> int:
        self._record("FDwfDigitalIOInputStatus", handle)
        self._set_value(input_mask, self.digital_input_status_mask)
        return self._result("FDwfDigitalIOInputStatus")

    def FDwfDigitalIOOutputEnableGet(self, handle: object, output_enable_mask: object) -> int:
        self._record("FDwfDigitalIOOutputEnableGet", handle)
        self._set_value(output_enable_mask, self.digital_output_enable_mask)
        return self._result("FDwfDigitalIOOutputEnableGet")

    def FDwfDigitalIOOutputGet(self, handle: object, output_mask: object) -> int:
        self._record("FDwfDigitalIOOutputGet", handle)
        self._set_value(output_mask, self.digital_output_mask)
        return self._result("FDwfDigitalIOOutputGet")

    def FDwfDigitalIOOutputEnableSet(self, handle: object, output_enable_mask: object) -> int:
        self._record("FDwfDigitalIOOutputEnableSet", handle, output_enable_mask)
        self.digital_output_enable_mask = self._value(output_enable_mask)
        return self._result("FDwfDigitalIOOutputEnableSet")

    def FDwfDigitalIOOutputSet(self, handle: object, output_mask: object) -> int:
        self._record("FDwfDigitalIOOutputSet", handle, output_mask)
        self.digital_output_mask = self._value(output_mask)
        return self._result("FDwfDigitalIOOutputSet")

    def FDwfDigitalIOConfigure(self, handle: object) -> int:
        self._record("FDwfDigitalIOConfigure", handle)
        return self._result("FDwfDigitalIOConfigure")

    def FDwfAnalogOutNodeFunctionGet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        function: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeFunctionGet", handle, channel_index, node_index)
        self._set_value(function, 1)
        return self._result("FDwfAnalogOutNodeFunctionGet")

    def FDwfAnalogOutNodeFrequencyGet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        frequency_hz: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeFrequencyGet", handle, channel_index, node_index)
        self._set_value(frequency_hz, 1000.0)
        return self._result("FDwfAnalogOutNodeFrequencyGet")

    def FDwfAnalogOutNodeAmplitudeGet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        amplitude_v: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeAmplitudeGet", handle, channel_index, node_index)
        self._set_value(amplitude_v, 1.0)
        return self._result("FDwfAnalogOutNodeAmplitudeGet")

    def FDwfAnalogOutNodeOffsetGet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        offset_v: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeOffsetGet", handle, channel_index, node_index)
        self._set_value(offset_v, 0.0)
        return self._result("FDwfAnalogOutNodeOffsetGet")

    def FDwfAnalogOutNodeSymmetryGet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        duty_cycle: object,
    ) -> int:
        self._record("FDwfAnalogOutNodeSymmetryGet", handle, channel_index, node_index)
        self._set_value(duty_cycle, 50.0)
        return self._result("FDwfAnalogOutNodeSymmetryGet")

    def FDwfAnalogOutNodePhaseGet(
        self,
        handle: object,
        channel_index: object,
        node_index: object,
        phase_degrees: object,
    ) -> int:
        self._record("FDwfAnalogOutNodePhaseGet", handle, channel_index, node_index)
        self._set_value(phase_degrees, 0.0)
        return self._result("FDwfAnalogOutNodePhaseGet")

    def FDwfGetLastErrorMsg(self, message: object) -> None:
        cast(Any, message).value = self.last_error.encode("utf-8")

    def _record(self, name: str, *args: object) -> None:
        self.calls.append((name, args))

    def _result(self, name: str) -> int:
        return 0 if self.fail_on == name else 1

    def _set_value(self, pointer: object, value: float | int) -> None:
        target = cast(Any, getattr(pointer, "_obj", pointer))
        target.value = value

    def _value(self, value: object) -> int:
        if isinstance(value, c_int):
            return int(value.value)
        if isinstance(value, c_byte):
            return int(value.value)
        if isinstance(value, c_uint):
            return int(value.value)
        if isinstance(value, c_double):
            return int(value.value)
        return int(cast(Any, value))


def test_real_capture_limits_query_opens_and_closes_device() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    limits = adapter.get_analog_capture_limits(device_index=3)

    assert limits.supported_channels == [1, 2]
    assert limits.default_sample_rate_hz == 1000.0
    assert limits.default_sample_count == 1000
    assert limits.max_sample_count_per_channel == 32_768
    assert limits.max_total_returned_samples == 65_536
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfAnalogInChannelCount",
        "FDwfAnalogInFrequencyInfo",
        "FDwfAnalogInBufferSizeInfo",
        "FDwfDeviceClose",
    ]


def test_real_capture_configures_requested_channels_and_returns_samples() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    capture = adapter.capture_analog_waveform(
        device_index=0,
        channel_indices=[0, 1],
        sample_rate_hz=2000.0,
        sample_count=4,
    )

    assert capture.sample_rate_hz == 999.5
    assert capture.sample_count == 4
    assert capture.channels == [1, 2]
    assert capture.samples == {
        "1": [0.0, 1.0, 2.0, 3.0],
        "2": [10.0, 11.0, 12.0, 13.0],
    }
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDeviceAutoConfigureSet",
        "FDwfAnalogInReset",
        "FDwfAnalogInChannelEnableSet",
        "FDwfAnalogInChannelEnableSet",
        "FDwfAnalogInAcquisitionModeSet",
        "FDwfAnalogInFrequencySet",
        "FDwfAnalogInBufferSizeSet",
        "FDwfAnalogInTriggerSourceSet",
        "FDwfAnalogInConfigure",
        "FDwfAnalogInStatus",
        "FDwfAnalogInFrequencyGet",
        "FDwfAnalogInStatusSamplesValid",
        "FDwfAnalogInStatusAutoTriggered",
        "FDwfAnalogInStatusRecord",
        "FDwfAnalogInStatusTime",
        "FDwfAnalogInStatusData",
        "FDwfAnalogInStatusData",
        "FDwfDeviceClose",
    ]


def test_real_capture_closes_device_when_sdk_call_fails() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.fail_on = "FDwfAnalogInFrequencySet"
    adapter = _adapter_with_sdk(sdk)

    with pytest.raises(DwfError, match="fake sdk failure"):
        adapter.capture_analog_waveform(
            device_index=0,
            channel_indices=[0],
            sample_rate_hz=2000.0,
            sample_count=4,
        )

    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_capture_configures_analog_edge_trigger() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    capture = adapter.capture_analog_waveform(
        device_index=0,
        channel_indices=[0],
        sample_rate_hz=1000.0,
        sample_count=4,
        trigger_config=AnalogTriggerConfig(
            channel=1,
            level_v=0.5,
            edge="rising",
            hysteresis_v=0.05,
            auto_timeout_seconds=1.0,
            position_seconds=0.002,
        ),
    )

    assert capture.triggered is True
    assert capture.auto_triggered is False
    assert capture.valid_sample_count == 4
    assert capture.lost_sample_count == 0
    assert capture.corrupt_sample_count == 0
    assert capture.status_time is not None
    assert "FDwfAnalogInTriggerSourceSet" in _call_names(sdk)
    assert "FDwfAnalogInTriggerConditionSet" in _call_names(sdk)


def test_real_analog_input_status_returns_capabilities() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    status = adapter.get_analog_input_status(device_index=0)

    assert status.channel_count == 2
    assert status.frequency_min_hz == 1.0
    assert status.frequency_max_hz == 100_000_000.0
    assert status.current_frequency_hz == 999.5
    assert status.buffer_size_min == 1
    assert status.buffer_size_max == 32_768
    assert status.current_buffer_size == 4096
    assert status.channel_ranges == {"1": 5.0, "2": 5.0}
    assert status.channel_offsets == {"1": 0.0, "2": 0.0}
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_capture_times_out() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.status_values = [1]
    adapter = _adapter_with_sdk(sdk)
    adapter._capture_timeout_seconds = 0.0  # type: ignore[attr-defined]

    with pytest.raises(DwfError, match="analog waveform capture timed out"):
        adapter.capture_analog_waveform(
            device_index=0,
            channel_indices=[0],
            sample_rate_hz=2000.0,
            sample_count=4,
        )

    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_limits_query_opens_and_closes_device() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    limits = adapter.get_wavegen_limits(device_index=0)

    assert limits.supported_channels == [1, 2]
    assert limits.supported_waveforms == ["sine", "square", "triangle", "dc", "custom"]
    assert limits.channel_limits["1"].frequency_min_hz == 0.1
    assert limits.channel_limits["1"].amplitude_max_v == 5.0
    assert limits.channel_limits["1"].custom_sample_count_min == 2
    assert limits.channel_limits["1"].custom_sample_count_max == 4096
    assert _call_names(sdk)[0] == "FDwfDeviceOpen"
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"
    assert "FDwfAnalogOutCount" in _call_names(sdk)
    assert "FDwfAnalogOutNodeFunctionInfo" in _call_names(sdk)
    assert "FDwfAnalogOutNodeDataInfo" in _call_names(sdk)


def test_real_digital_io_limits_query_opens_and_closes_device() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.digital_input_info_mask = 0b1011
    sdk.digital_output_enable_info_mask = 0b1111
    sdk.digital_output_info_mask = 0b0101
    adapter = _adapter_with_sdk(sdk)

    limits = adapter.get_digital_io_limits(device_index=0)

    assert limits.supported_input_pins == [0, 1, 3]
    assert limits.supported_output_pins == [0, 2]
    assert limits.input_mask == 0b1011
    assert limits.output_enable_mask == 0b0101
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDigitalIOInputInfo",
        "FDwfDigitalIOOutputEnableInfo",
        "FDwfDigitalIOOutputInfo",
        "FDwfDeviceClose",
    ]


def test_real_digital_input_read_returns_selected_pin_values() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.digital_input_status_mask = 0b1010
    adapter = _adapter_with_sdk(sdk)

    read = adapter.read_digital_inputs(device_index=0, pins=[0, 1, 3])

    assert read.pins == [0, 1, 3]
    assert read.values == {"0": False, "1": True, "3": True}
    assert read.input_mask == 0b1010
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDigitalIOStatus",
        "FDwfDigitalIOInputStatus",
        "FDwfDeviceClose",
    ]


def test_real_digital_output_write_preserves_existing_state() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.digital_output_enable_mask = 0b1000
    sdk.digital_output_mask = 0b1000
    adapter = _adapter_with_sdk(sdk)

    status = adapter.write_digital_outputs(
        device_index=0,
        pins=[0, 3],
        values=[True, False],
    )

    assert status.pins == [0, 3]
    assert status.values == {"0": True, "3": False}
    assert status.output_enable_mask == 0b1001
    assert status.output_mask == 0b0001
    assert sdk.digital_output_enable_mask == 0b1001
    assert sdk.digital_output_mask == 0b0001
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDigitalIOOutputEnableGet",
        "FDwfDigitalIOOutputGet",
        "FDwfDigitalIOOutputEnableSet",
        "FDwfDigitalIOOutputSet",
        "FDwfDigitalIOConfigure",
    ]
    adapter.close()
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_digital_output_write_can_replace_existing_state() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.digital_output_enable_mask = 0b1000
    sdk.digital_output_mask = 0b1000
    adapter = _adapter_with_sdk(sdk)

    status = adapter.write_digital_outputs(
        device_index=0,
        pins=[1],
        values=[True],
        preserve_existing=False,
    )

    assert status.output_enable_mask == 0b0010
    assert status.output_mask == 0b0010
    assert sdk.digital_output_enable_mask == 0b0010
    assert sdk.digital_output_mask == 0b0010
    assert _call_names(sdk)[-1] == "FDwfDigitalIOConfigure"
    adapter.close()
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_digital_io_closes_device_when_sdk_call_fails() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.fail_on = "FDwfDigitalIOOutputSet"
    adapter = _adapter_with_sdk(sdk)

    with pytest.raises(DwfError, match="fake sdk failure"):
        adapter.write_digital_outputs(device_index=0, pins=[0], values=[True])

    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_start_configures_output() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    status = adapter.start_wavegen(
        device_index=0,
        config=WavegenConfig(
            channel=2,
            waveform="square",
            frequency_hz=2000.0,
            amplitude_v=1.5,
            offset_v=0.25,
            duty_cycle_percent=40.0,
        ),
    )

    assert status.running is True
    assert status.channel == 2
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDeviceAutoConfigureSet",
        "FDwfAnalogOutReset",
        "FDwfAnalogOutNodeEnableSet",
        "FDwfAnalogOutNodeFunctionSet",
        "FDwfAnalogOutNodeFrequencySet",
        "FDwfAnalogOutNodeAmplitudeSet",
        "FDwfAnalogOutNodeOffsetSet",
        "FDwfAnalogOutNodeSymmetrySet",
        "FDwfAnalogOutConfigure",
    ]
    adapter.close()
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_start_configures_custom_output() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    status = adapter.start_wavegen(
        device_index=0,
        config=WavegenConfig(
            channel=1,
            waveform="custom",
            frequency_hz=1000.0,
            amplitude_v=1.5,
            offset_v=0.25,
            duty_cycle_percent=50.0,
            samples=[-1.0, 0.0, 1.0, 0.0],
            sample_rate_hz=4000.0,
        ),
    )

    assert status.running is True
    assert status.config is not None
    assert status.config.waveform == "custom"
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDeviceAutoConfigureSet",
        "FDwfAnalogOutReset",
        "FDwfAnalogOutNodeEnableSet",
        "FDwfAnalogOutNodeFunctionSet",
        "FDwfAnalogOutNodeDataSet",
        "FDwfAnalogOutNodeFrequencySet",
        "FDwfAnalogOutNodeAmplitudeSet",
        "FDwfAnalogOutNodeOffsetSet",
        "FDwfAnalogOutNodeSymmetrySet",
        "FDwfAnalogOutConfigure",
    ]
    adapter.close()
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_synchronized_wavegen_configures_master_and_phase() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    statuses = adapter.start_synchronized_wavegen(
        device_index=0,
        configs=[
            WavegenConfig(
                channel=1,
                waveform="sine",
                frequency_hz=1000.0,
                amplitude_v=2.0,
                offset_v=0.0,
                duty_cycle_percent=50.0,
                phase_degrees=0.0,
            ),
            WavegenConfig(
                channel=2,
                waveform="sine",
                frequency_hz=1000.0,
                amplitude_v=2.0,
                offset_v=0.0,
                duty_cycle_percent=50.0,
                phase_degrees=180.0,
            ),
        ],
        master_channel=1,
    )

    assert [status.channel for status in statuses] == [1, 2]
    assert all(status.running for status in statuses)
    assert _call_names(sdk) == [
        "FDwfDeviceOpen",
        "FDwfDeviceAutoConfigureSet",
        "FDwfAnalogOutReset",
        "FDwfAnalogOutReset",
        "FDwfAnalogOutNodeEnableSet",
        "FDwfAnalogOutNodeFunctionSet",
        "FDwfAnalogOutNodeFrequencySet",
        "FDwfAnalogOutNodeAmplitudeSet",
        "FDwfAnalogOutNodeOffsetSet",
        "FDwfAnalogOutNodeSymmetrySet",
        "FDwfAnalogOutNodePhaseSet",
        "FDwfAnalogOutMasterSet",
        "FDwfAnalogOutNodeEnableSet",
        "FDwfAnalogOutNodeFunctionSet",
        "FDwfAnalogOutNodeFrequencySet",
        "FDwfAnalogOutNodeAmplitudeSet",
        "FDwfAnalogOutNodeOffsetSet",
        "FDwfAnalogOutNodeSymmetrySet",
        "FDwfAnalogOutNodePhaseSet",
        "FDwfAnalogOutConfigure",
        "FDwfAnalogOutConfigure",
    ]
    adapter.close()
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_synchronized_wavegen_closes_device_when_sdk_call_fails() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.fail_on = "FDwfAnalogOutNodePhaseSet"
    adapter = _adapter_with_sdk(sdk)

    with pytest.raises(DwfError, match="fake sdk failure"):
        adapter.start_synchronized_wavegen(
            device_index=0,
            configs=[
                WavegenConfig(
                    channel=1,
                    waveform="sine",
                    frequency_hz=1000.0,
                    amplitude_v=1.0,
                    offset_v=0.0,
                    duty_cycle_percent=50.0,
                    phase_degrees=0.0,
                ),
                WavegenConfig(
                    channel=2,
                    waveform="sine",
                    frequency_hz=1000.0,
                    amplitude_v=1.0,
                    offset_v=0.0,
                    duty_cycle_percent=50.0,
                    phase_degrees=180.0,
                ),
            ],
            master_channel=1,
        )

    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_stop_reads_status_and_closes_temporary_device() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    status = adapter.stop_wavegen(device_index=0, channel=1)

    assert status.running is False
    assert status.config is not None
    assert status.config.waveform == "sine"
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"
    assert "FDwfAnalogOutConfigure" in _call_names(sdk)
    assert "FDwfAnalogOutStatus" in _call_names(sdk)


def test_real_wavegen_stop_keeps_handle_open_for_other_active_channel() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    adapter.start_wavegen(
        device_index=0,
        config=WavegenConfig(
            channel=1,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=1.0,
            offset_v=0.0,
            duty_cycle_percent=50.0,
        ),
    )
    adapter.start_wavegen(
        device_index=0,
        config=WavegenConfig(
            channel=2,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=1.0,
            offset_v=0.0,
            duty_cycle_percent=50.0,
        ),
    )

    status = adapter.stop_wavegen(device_index=0, channel=1)
    adapter.get_wavegen_status(device_index=0, channel=2)

    assert status.running is False
    assert _call_names(sdk).count("FDwfDeviceOpen") == 1
    assert _call_names(sdk)[-1] != "FDwfDeviceClose"
    released = adapter.release_device(device_index=0)
    assert released.released is True
    assert released.wavegen_channels_stopped == [2]
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_stop_keeps_handle_open_for_active_digital_outputs() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    adapter.start_wavegen(
        device_index=0,
        config=WavegenConfig(
            channel=1,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=1.0,
            offset_v=0.0,
            duty_cycle_percent=50.0,
        ),
    )
    adapter.write_digital_outputs(device_index=0, pins=[0], values=[True])
    status = adapter.stop_wavegen(device_index=0, channel=1)
    adapter.read_digital_inputs(device_index=0, pins=[0])

    assert status.running is False
    assert sdk.digital_output_enable_mask == 0b1
    assert _call_names(sdk).count("FDwfDeviceOpen") == 1
    assert _call_names(sdk)[-1] != "FDwfDeviceClose"
    released = adapter.release_device(device_index=0)
    assert released.released is True
    assert released.wavegen_channels_stopped == []
    assert sdk.digital_output_enable_mask == 0
    assert sdk.digital_output_mask == 0
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_release_device_is_idempotent() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    first = adapter.release_device(device_index=0)
    second = adapter.release_device(device_index=0)

    assert first.released is False
    assert second.released is False
    assert first.wavegen_channels_stopped == []
    assert second.digital_output_enable_mask == 0
    assert _call_names(sdk) == []


def test_real_release_device_stops_outputs_and_closes_handle() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    adapter.start_wavegen(
        device_index=0,
        config=WavegenConfig(
            channel=1,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=1.0,
            offset_v=0.0,
            duty_cycle_percent=50.0,
        ),
    )
    adapter.write_digital_outputs(device_index=0, pins=[0, 1], values=[True, False])

    released = adapter.release_device(device_index=0)

    assert released.released is True
    assert released.wavegen_channels_stopped == [1]
    assert released.digital_output_enable_mask == 0
    assert sdk.digital_output_enable_mask == 0
    assert sdk.digital_output_mask == 0
    assert _call_names(sdk)[-5:] == [
        "FDwfAnalogOutConfigure",
        "FDwfDigitalIOOutputEnableSet",
        "FDwfDigitalIOOutputSet",
        "FDwfDigitalIOConfigure",
        "FDwfDeviceClose",
    ]


def test_real_wavegen_status_returns_running_config() -> None:
    sdk = FakeWaveFormsSdk()
    adapter = _adapter_with_sdk(sdk)

    status = adapter.get_wavegen_status(device_index=0, channel=1)

    assert status.running is True
    assert status.state == 3
    assert status.config is not None
    assert status.config.frequency_hz == 1000.0
    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_closes_device_when_sdk_call_fails() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.fail_on = "FDwfAnalogOutNodeFrequencySet"
    adapter = _adapter_with_sdk(sdk)

    with pytest.raises(DwfError, match="fake sdk failure"):
        adapter.start_wavegen(
            device_index=0,
            config=WavegenConfig(
                channel=1,
                waveform="sine",
                frequency_hz=1000.0,
                amplitude_v=1.0,
                offset_v=0.0,
                duty_cycle_percent=50.0,
            ),
        )

    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def test_real_wavegen_closes_device_when_custom_upload_fails() -> None:
    sdk = FakeWaveFormsSdk()
    sdk.fail_on = "FDwfAnalogOutNodeDataSet"
    adapter = _adapter_with_sdk(sdk)

    with pytest.raises(DwfError, match="fake sdk failure"):
        adapter.start_wavegen(
            device_index=0,
            config=WavegenConfig(
                channel=1,
                waveform="custom",
                frequency_hz=1000.0,
                amplitude_v=1.0,
                offset_v=0.0,
                duty_cycle_percent=50.0,
                samples=[0.0, 1.0],
                sample_rate_hz=2000.0,
            ),
        )

    assert _call_names(sdk)[-1] == "FDwfDeviceClose"


def _adapter_with_sdk(sdk: FakeWaveFormsSdk) -> CtypesDwfAdapter:
    adapter = CtypesDwfAdapter.__new__(CtypesDwfAdapter)
    adapter._dwf = sdk
    return adapter


def _call_names(sdk: FakeWaveFormsSdk) -> list[str]:
    return [name for name, _args in sdk.calls]
