from __future__ import annotations

import pytest

from analog_discovery_mcp.dwf import CtypesDwfAdapter
from analog_discovery_mcp.service import AnalogDiscoveryService

pytestmark = pytest.mark.hardware


@pytest.mark.hardware_stand("basic")
def test_hardware_can_list_devices() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.list_devices()

    assert result.ok is True
    assert result.data is not None
    assert "devices" in result.data


@pytest.mark.hardware_stand("basic")
def test_hardware_can_capture_small_analog_waveform() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.capture_analog_waveform(
        channels=[1],
        sample_rate_hz=1000.0,
        sample_count=16,
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["channels"] == [1]
    assert result.data["sample_count"] == 16
    assert len(result.data["samples"]["1"]) == 16


@pytest.mark.hardware_stand("basic")
def test_hardware_can_report_analog_input_status() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.get_analog_input_status()

    assert result.ok is True
    assert result.data is not None
    assert result.data["channel_count"] >= 1
    assert result.data["buffer_size_max"] >= result.data["buffer_size_min"]


@pytest.mark.hardware_stand("basic")
def test_hardware_can_report_wavegen_limits() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.get_wavegen_limits()

    assert result.ok is True
    assert result.data is not None
    assert result.data["supported_channels"]
    assert "sine" in result.data["supported_waveforms"]


@pytest.mark.hardware_stand("basic")
def test_hardware_can_measure_analog_waveform() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.measure_analog_waveform(channel=1, sample_rate_hz=1000.0, sample_count=16)

    assert result.ok is True
    assert result.data is not None
    assert "samples" not in result.data
    assert result.data["channel"] == 1
    assert result.data["max_voltage"] >= result.data["min_voltage"]


@pytest.mark.hardware_stand("analog-loopback")
def test_hardware_can_capture_with_analog_trigger() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.capture_analog_waveform(
        channels=[1],
        sample_rate_hz=1000.0,
        sample_count=64,
        trigger_enabled=True,
        trigger_level_v=0.5,
        trigger_edge="rising",
        trigger_auto_timeout_seconds=2.0,
    )

    assert result.ok is True
    assert result.data is not None
    assert result.data["channels"] == [1]
    assert len(result.data["samples"]["1"]) == 64
    assert result.data["triggered"] is True
    assert result.data["auto_triggered"] is False


@pytest.mark.hardware_stand("analog-loopback")
def test_hardware_can_start_and_stop_wavegen() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    try:
        start = service.start_wavegen(
            channel=1,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=0.5,
            offset_v=0.0,
        )
        assert start.ok is True
        assert start.data is not None
        assert start.data["running"] is True

        capture = service.measure_analog_waveform(
            channel=1,
            sample_rate_hz=10_000.0,
            sample_count=128,
        )
        assert capture.ok is True
        assert capture.data is not None
        assert capture.data["peak_to_peak_voltage"] > 0.1
    finally:
        stop = service.stop_wavegen(channel=1)
        assert stop.ok is True
