from __future__ import annotations

from analog_discovery_mcp.fake import FakeDwfAdapter
from analog_discovery_mcp.service import AnalogDiscoveryService


def test_fake_adapter_reports_version() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.get_waveforms_version()

    assert result.ok is True
    assert result.data == {"version": "fake-0.1.0"}


def test_fake_adapter_lists_fake_ad3() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.list_devices()

    assert result.ok is True
    assert result.data == {
        "devices": [
            {
                "index": 0,
                "name": "Analog Discovery 3 (Fake)",
                "serial_number": "FAKE-AD3-0001",
                "available": True,
            }
        ]
    }


def test_fake_adapter_reads_deterministic_channel_one_voltage() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.read_analog_voltage(channel=1)

    assert result.ok is True
    assert result.data is not None
    assert result.data["voltage"] == 1.25


def test_fake_adapter_reads_deterministic_channel_two_voltage() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.read_analog_voltage(channel=2)

    assert result.ok is True
    assert result.data is not None
    assert result.data["voltage"] == 2.50


def test_fake_adapter_reports_capture_limits() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.get_analog_capture_limits()

    assert result.ok is True
    assert result.data is not None
    assert result.data["supported_channels"] == [1, 2]
    assert result.data["default_sample_rate_hz"] == 1000.0
    assert result.data["default_sample_count"] == 1000
    assert result.data["max_sample_count_per_channel"] == 32_768
    assert result.data["max_total_returned_samples"] == 65_536


def test_fake_adapter_captures_deterministic_waveform() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.capture_analog_waveform(channels=[1, 2], sample_count=4)

    assert result.ok is True
    assert result.data is not None
    assert result.data["requested_sample_rate_hz"] == 1000.0
    assert result.data["actual_sample_rate_hz"] == 1000.0
    assert result.data["sample_count"] == 4
    assert result.data["duration_seconds"] == 0.004
    assert result.data["channels"] == [1, 2]
    assert result.data["samples"]["1"] == [0.0, 0.124675, 0.247404, 0.366273]
    assert result.data["samples"]["2"] == [0.5, 0.496099, 0.484456, 0.465254]
