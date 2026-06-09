from __future__ import annotations

from ctypes import c_double, c_int
from typing import Any, cast

import pytest

from analog_discovery_mcp.dwf import CtypesDwfAdapter, DwfError


class FakeWaveFormsSdk:
    def __init__(self) -> None:
        self.calls: list[tuple[str, tuple[object, ...]]] = []
        self.status_values = [2]
        self.fail_on: str | None = None
        self.last_error = "fake sdk failure"

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
        "FDwfAnalogInConfigure",
        "FDwfAnalogInStatus",
        "FDwfAnalogInFrequencyGet",
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


def _adapter_with_sdk(sdk: FakeWaveFormsSdk) -> CtypesDwfAdapter:
    adapter = CtypesDwfAdapter.__new__(CtypesDwfAdapter)
    adapter._dwf = sdk
    return adapter


def _call_names(sdk: FakeWaveFormsSdk) -> list[str]:
    return [name for name, _args in sdk.calls]
