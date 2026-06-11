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
    assert result.data["triggered"] is False
    assert adapter.capture_calls == [(0, [0], 1000.0, 1000, None)]


def test_capture_passes_normalized_trigger_config(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.capture_analog_waveform(
        channels=[1],
        sample_count=10,
        trigger_enabled=True,
        trigger_level_v=0.5,
        trigger_edge="RISING",
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["triggered"] is True
    assert result.data["trigger"] == {
        "channel": 1,
        "level_v": 0.5,
        "edge": "rising",
        "hysteresis_v": 0.05,
        "auto_timeout_seconds": 1.0,
        "position_seconds": 0.005,
    }
    assert adapter.capture_calls[0][4] is not None


def test_capture_rejects_invalid_trigger_edge(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(trigger_enabled=True, trigger_edge="both")

    assert result.ok is False
    assert result.error == "trigger_edge must be 'rising' or 'falling'"


def test_capture_rejects_trigger_channel_outside_capture(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(
        channels=[1],
        trigger_enabled=True,
        trigger_channel=2,
    )

    assert result.ok is False
    assert result.error == "trigger_channel must be included in channels"


def test_capture_rejects_invalid_trigger_hysteresis(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(
        trigger_enabled=True,
        trigger_hysteresis_v=0,
    )

    assert result.ok is False
    assert result.error == "trigger_hysteresis_v must be positive"


def test_capture_rejects_invalid_trigger_timeout(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(
        trigger_enabled=True,
        trigger_auto_timeout_seconds=0,
    )

    assert result.ok is False
    assert result.error == "trigger_auto_timeout_seconds must be positive"


def test_capture_rejects_invalid_trigger_position(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.capture_analog_waveform(
        trigger_enabled=True,
        sample_count=10,
        sample_rate_hz=1000.0,
        trigger_position_seconds=1.0,
    )

    assert result.ok is False
    assert result.error == "trigger_position_seconds must be between 0 and 0.01"


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


def test_measure_analog_waveform_returns_core_stats_without_samples(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.measure_analog_waveform(channel=1, sample_count=4)

    assert result.ok is True
    assert result.data is not None
    assert "samples" not in result.data
    assert result.data["channel"] == 1
    assert result.data["min_voltage"] == 1.0
    assert result.data["max_voltage"] == 1.0
    assert result.data["mean_voltage"] == 1.0
    assert result.data["rms_voltage"] == 1.0
    assert result.data["peak_to_peak_voltage"] == 0.0


def test_get_analog_input_status_returns_status_shape(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.get_analog_input_status()

    assert result.ok is True
    assert result.data is not None
    assert result.data["channel_count"] == 2
    assert result.data["frequency_min_hz"] == 1.0
    assert result.data["buffer_size_max"] == 32_768
    assert result.data["channel_ranges"] == {"1": 5.0, "2": 5.0}
    assert result.data["device"]["serial_number"] == "SN:AD2"


def test_get_wavegen_limits_returns_status_shape(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.get_wavegen_limits()

    assert result.ok is True
    assert result.data is not None
    assert result.data["supported_channels"] == [1, 2]
    assert result.data["supported_waveforms"] == ["sine", "square", "triangle", "dc", "custom"]
    assert result.data["channel_limits"]["1"]["amplitude_max_v"] == 5.0
    assert result.data["channel_limits"]["1"]["custom_sample_count_max"] == 4096
    assert result.data["device"]["serial_number"] == "SN:AD2"


def test_start_wavegen_uses_defaults(sample_devices: list[DeviceInfo]) -> None:
    adapter = FakeDwfAdapter(devices=sample_devices)
    service = AnalogDiscoveryService(adapter, environ={})

    result = service.start_wavegen()

    assert result.ok is True
    assert result.data is not None
    assert result.data["running"] is True
    assert result.data["config"] == {
        "channel": 1,
        "waveform": "sine",
        "frequency_hz": 1000.0,
        "amplitude_v": 1.0,
        "offset_v": 0.0,
        "duty_cycle_percent": 50.0,
    }
    assert adapter.wavegen_calls[0][0] == "start"


def test_start_wavegen_normalizes_dc_amplitude(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(waveform="DC", offset_v=1.25, amplitude_v=3.0)

    assert result.ok is True
    assert result.data is not None
    assert result.data["config"]["waveform"] == "dc"
    assert result.data["config"]["amplitude_v"] == 0.0
    assert result.data["config"]["offset_v"] == 1.25


def test_start_wavegen_accepts_custom_samples(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(
        waveform="custom",
        samples=[-1.0, 0.0, 1.0, 0.0],
        sample_rate_hz=4000.0,
        amplitude_v=2.0,
        offset_v=0.25,
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["config"]["waveform"] == "custom"
    assert result.data["config"]["samples"] == [-1.0, 0.0, 1.0, 0.0]
    assert result.data["config"]["sample_rate_hz"] == 4000.0
    assert result.data["config"]["frequency_hz"] == 1000.0
    assert result.data["config"]["amplitude_v"] == 2.0
    assert result.data["config"]["offset_v"] == 0.25


def test_start_wavegen_rejects_invalid_channel(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(channel=3)

    assert result.ok is False
    assert result.error == "channel must be one of [1, 2]; got 3"


def test_start_wavegen_rejects_invalid_waveform(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(waveform="noise")

    assert result.ok is False
    assert result.error == (
        "waveform must be one of ['sine', 'square', 'triangle', 'dc', 'custom']; got 'noise'"
    )


def test_start_wavegen_rejects_non_finite_value(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(frequency_hz=float("nan"))

    assert result.ok is False
    assert result.error == "frequency_hz must be finite"


def test_start_wavegen_rejects_out_of_range_frequency(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(frequency_hz=0.0)

    assert result.ok is False
    assert result.error == "frequency_hz must be between 0.1 and 10000000.0"


def test_start_wavegen_rejects_out_of_range_amplitude(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(amplitude_v=6.0)

    assert result.ok is False
    assert result.error == "amplitude_v must be between 0.0 and 5.0"


def test_start_wavegen_rejects_out_of_range_offset(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(offset_v=6.0)

    assert result.ok is False
    assert result.error == "offset_v must be between -5.0 and 5.0"


def test_start_wavegen_rejects_out_of_range_duty_cycle(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(duty_cycle_percent=101.0)

    assert result.ok is False
    assert result.error == "duty_cycle_percent must be between 0.0 and 100.0"


def test_start_wavegen_rejects_custom_without_samples(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(waveform="custom", sample_rate_hz=1000.0)

    assert result.ok is False
    assert result.error == "samples are required for custom waveform"


def test_start_wavegen_rejects_custom_without_sample_rate(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(waveform="custom", samples=[0.0, 1.0])

    assert result.ok is False
    assert result.error == "sample_rate_hz is required for custom waveform"


def test_start_wavegen_rejects_non_finite_custom_sample(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(
        waveform="custom",
        samples=[0.0, float("nan")],
        sample_rate_hz=1000.0,
    )

    assert result.ok is False
    assert result.error == "samples must be finite"


def test_start_wavegen_rejects_out_of_range_custom_sample(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(
        waveform="custom",
        samples=[0.0, 1.1],
        sample_rate_hz=1000.0,
    )

    assert result.ok is False
    assert result.error == "samples must be between -1.0 and 1.0"


def test_start_wavegen_rejects_custom_sample_count(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(
        waveform="custom",
        samples=[0.0],
        sample_rate_hz=1000.0,
    )

    assert result.ok is False
    assert result.error == "samples length must be between 2 and 4096"


def test_start_wavegen_rejects_custom_frequency_out_of_range(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(
        waveform="custom",
        samples=[0.0, 1.0],
        sample_rate_hz=0.1,
    )

    assert result.ok is False
    assert result.error == "sample_rate_hz / len(samples) must be between 0.1 and 10000000.0"


def test_start_wavegen_rejects_samples_for_builtin_waveform(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(waveform="sine", samples=[0.0, 1.0])

    assert result.ok is False
    assert result.error == "samples are only supported for custom waveform"


def test_start_wavegen_rejects_sample_rate_for_builtin_waveform(
    sample_devices: list[DeviceInfo],
) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    result = service.start_wavegen(waveform="sine", sample_rate_hz=1000.0)

    assert result.ok is False
    assert result.error == "sample_rate_hz is only supported for custom waveform"


def test_stop_wavegen_returns_last_config(sample_devices: list[DeviceInfo]) -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(devices=sample_devices), environ={})

    service.start_wavegen(channel=2, waveform="triangle")
    result = service.stop_wavegen(channel=2)

    assert result.ok is True
    assert result.data is not None
    assert result.data["running"] is False
    assert result.data["config"]["waveform"] == "triangle"
