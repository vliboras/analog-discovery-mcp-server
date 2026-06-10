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
    assert result.data["valid_sample_count"] == 4
    assert result.data["lost_sample_count"] == 0


def test_fake_adapter_measures_core_stats() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.measure_analog_waveform(channel=2, sample_count=1)

    assert result.ok is True
    assert result.data is not None
    assert "samples" not in result.data
    assert result.data["min_voltage"] == 0.5
    assert result.data["max_voltage"] == 0.5
    assert result.data["mean_voltage"] == 0.5
    assert result.data["rms_voltage"] == 0.5
    assert result.data["peak_to_peak_voltage"] == 0.0


def test_fake_adapter_reports_analog_input_status() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.get_analog_input_status()

    assert result.ok is True
    assert result.data is not None
    assert result.data["channel_count"] == 2
    assert result.data["current_frequency_hz"] == 1000.0
    assert result.data["channel_ranges"] == {"1": 5.0, "2": 5.0}


def test_fake_adapter_reports_wavegen_limits() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    result = service.get_wavegen_limits()

    assert result.ok is True
    assert result.data is not None
    assert result.data["supported_channels"] == [1, 2]
    assert result.data["supported_waveforms"] == ["sine", "square", "triangle", "dc"]
    assert result.data["default_waveform"] == "sine"


def test_fake_adapter_tracks_wavegen_state() -> None:
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    started = service.start_wavegen(channel=1, waveform="square", frequency_hz=2000.0)
    status = service.get_wavegen_status(channel=1)
    stopped = service.stop_wavegen(channel=1)

    assert started.ok is True
    assert started.data is not None
    assert started.data["running"] is True
    assert started.data["config"]["waveform"] == "square"
    assert started.data["config"]["frequency_hz"] == 2000.0
    assert status.ok is True
    assert status.data is not None
    assert status.data["running"] is True
    assert stopped.ok is True
    assert stopped.data is not None
    assert stopped.data["running"] is False
    assert stopped.data["config"]["waveform"] == "square"
