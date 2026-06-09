from __future__ import annotations

from analog_discovery_mcp.dwf import DwfError
from analog_discovery_mcp.models import AnalogCaptureLimits, DeviceInfo
from analog_discovery_mcp.service import (
    ENV_DEVICE_INDEX,
    ENV_DEVICE_SERIAL,
    AnalogDiscoveryService,
)
from tests.conftest import FakeDwfAdapter


def test_get_waveforms_version_success() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(version="3.24.3"), environ={})

    result = service.get_waveforms_version()

    assert result.ok is True
    assert result.data == {"version": "3.24.3"}


def test_get_waveforms_version_reports_sdk_error(sdk_missing_error: DwfError) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(fail_version=sdk_missing_error), environ={})

    result = service.get_waveforms_version()

    assert result.ok is False
    assert result.error == "Unable to load WaveForms SDK library: libdwf.so"


def test_list_devices_zero() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=[]), environ={})

    result = service.list_devices()

    assert result.ok is True
    assert result.data == {"devices": []}


def test_list_devices_multiple(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.list_devices()

    assert result.ok is True
    assert result.data == {
        "devices": [
            {
                "index": 0,
                "name": "Analog Discovery 2",
                "serial_number": "SN:AD2",
                "available": True,
            },
            {
                "index": 1,
                "name": "Analog Discovery 3",
                "serial_number": "SN:AD3",
                "available": True,
            },
        ]
    }


def test_read_voltage_selects_explicit_index(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices, read_voltage=2.5)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.read_analog_voltage(channel=2, device_index=1)

    assert result.ok is True
    assert result.data is not None
    assert result.data["voltage"] == 2.5
    assert result.data["unit"] == "V"
    assert result.data["channel"] == 2
    assert result.data["device"]["serial_number"] == "SN:AD3"
    assert adapter.read_calls == [(1, 1)]


def test_read_voltage_selects_explicit_serial(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.read_analog_voltage(channel=1, serial_number="SN:AD3")

    assert result.ok is True
    assert adapter.read_calls == [(1, 0)]


def test_read_voltage_uses_env_index(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={ENV_DEVICE_INDEX: "1"})

    result = service.read_analog_voltage(channel=1)

    assert result.ok is True
    assert adapter.read_calls == [(1, 0)]


def test_read_voltage_uses_env_serial(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={ENV_DEVICE_SERIAL: "SN:AD3"})

    result = service.read_analog_voltage(channel=1)

    assert result.ok is True
    assert adapter.read_calls == [(1, 0)]


def test_read_voltage_defaults_to_first_device(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.read_analog_voltage(channel=1)

    assert result.ok is True
    assert adapter.read_calls == [(0, 0)]


def test_read_voltage_rejects_invalid_channel(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.read_analog_voltage(channel=3)

    assert result.ok is False
    assert result.error == "channel must be 1 or 2"
    assert adapter.read_calls == []


def test_read_voltage_rejects_conflicting_tool_selection(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.read_analog_voltage(channel=1, device_index=0, serial_number="SN:AD2")

    assert result.ok is False
    assert result.error == "Use either device_index or serial_number, not both"


def test_read_voltage_rejects_conflicting_env_selection(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(
        FakeDwfAdapter(devices=sample_devices),
        environ={ENV_DEVICE_INDEX: "0", ENV_DEVICE_SERIAL: "SN:AD2"},
    )

    result = service.read_analog_voltage(channel=1)

    assert result.ok is False
    assert result.error == f"Set only one of {ENV_DEVICE_INDEX} or {ENV_DEVICE_SERIAL}"


def test_read_voltage_rejects_invalid_env_index(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(
        FakeDwfAdapter(devices=sample_devices),
        environ={ENV_DEVICE_INDEX: "first"},
    )

    result = service.read_analog_voltage(channel=1)

    assert result.ok is False
    assert result.error == f"{ENV_DEVICE_INDEX} must be an integer"


def test_read_voltage_reports_no_devices() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=[]), environ={})

    result = service.read_analog_voltage(channel=1)

    assert result.ok is False
    assert result.error == "No WaveForms devices found"


def test_read_voltage_reports_missing_serial(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.read_analog_voltage(channel=1, serial_number="missing")

    assert result.ok is False
    assert result.error == "No WaveForms device found with serial number 'missing'"


def test_read_voltage_reports_missing_index(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.read_analog_voltage(channel=1, device_index=99)

    assert result.ok is False
    assert result.error == "No WaveForms device found at index 99"


def test_read_voltage_reports_sdk_read_error(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices, fail_read=DwfError("read failed"))
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.read_analog_voltage(channel=1)

    assert result.ok is False
    assert result.error == "read failed"
    assert adapter.read_calls == [(0, 0)]


def test_capture_uses_defaults(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.capture_analog_waveform()

    assert result.ok is True
    assert result.data is not None
    assert result.data["sample_count"] == 1000
    assert result.data["channels"] == [1]
    assert len(result.data["samples"]["1"]) == 1000
    assert adapter.capture_calls == [(0, [0], 1000.0, 1000)]


def test_capture_rejects_empty_channels(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(channels=[])

    assert result.ok is False
    assert result.error == "channels must not be empty"


def test_capture_rejects_duplicate_channels(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(channels=[1, 1])

    assert result.ok is False
    assert result.error == "channels must not contain duplicates"


def test_capture_rejects_unsupported_channels(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(channels=[3])

    assert result.ok is False
    assert result.error == "channels must only contain supported channels [1, 2]; got [3]"


def test_capture_rejects_invalid_sample_rate(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(sample_rate_hz=0)

    assert result.ok is False
    assert result.error == "sample_rate_hz must be positive"


def test_capture_rejects_invalid_sample_count(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(sample_count=32_769)

    assert result.ok is False
    assert result.error == "sample_count must be between 1 and 32768"


def test_capture_rejects_excessive_total_samples(sample_devices: list[DeviceInfo]) -> None:
    class LowTotalLimitAdapter(FakeDwfAdapter):
        def get_analog_capture_limits(self, device_index: int) -> AnalogCaptureLimits:
            return AnalogCaptureLimits(
                supported_channels=[1, 2],
                default_sample_rate_hz=1000.0,
                default_sample_count=1000,
                max_sample_count_per_channel=32_768,
                max_total_returned_samples=8,
            )

    service = AnalogDiscoveryService(LowTotalLimitAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(channels=[1, 2], sample_count=5)

    assert result.ok is False
    assert result.error == "total returned samples must be at most 8"

