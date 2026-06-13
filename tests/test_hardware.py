from __future__ import annotations

import math
import statistics
from itertools import pairwise

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
def test_hardware_can_report_digital_io_limits() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.get_digital_io_limits()

    assert result.ok is True
    assert result.data is not None
    assert result.data["supported_input_pins"]
    assert result.data["supported_output_pins"]


@pytest.mark.hardware_stand("basic")
def test_hardware_can_read_digital_inputs() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    limits = service.get_digital_io_limits()
    assert limits.ok is True
    assert limits.data is not None
    pin = limits.data["supported_input_pins"][0]

    result = service.read_digital_inputs(pins=[pin])

    assert result.ok is True
    assert result.data is not None
    assert result.data["pins"] == [pin]
    assert str(pin) in result.data["values"]


@pytest.mark.hardware_stand("basic")
def test_hardware_can_measure_analog_waveform() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.measure_analog_waveform(channel=1, sample_rate_hz=1000.0, sample_count=16)

    assert result.ok is True
    assert result.data is not None
    assert "samples" not in result.data
    assert result.data["channel"] == 1
    assert result.data["max_voltage"] >= result.data["min_voltage"]


@pytest.mark.hardware_stand("advanced")
def test_hardware_can_capture_with_analog_trigger() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    try:
        start = service.start_wavegen(
            channel=1,
            waveform="sine",
            frequency_hz=100.0,
            amplitude_v=1.0,
            offset_v=0.0,
        )
        assert start.ok is True

        result = service.capture_analog_waveform(
            channels=[1],
            sample_rate_hz=1000.0,
            sample_count=64,
            trigger_enabled=True,
            trigger_level_v=0.0,
            trigger_edge="rising",
            trigger_auto_timeout_seconds=2.0,
        )
    finally:
        stop = service.stop_wavegen(channel=1)
        assert stop.ok is True

    assert result.ok is True
    assert result.data is not None
    assert result.data["channels"] == [1]
    assert len(result.data["samples"]["1"]) == 64
    assert result.data["triggered"] is True
    assert result.data["auto_triggered"] is False


@pytest.mark.hardware_stand("advanced")
@pytest.mark.parametrize("channel", [1, 2])
def test_hardware_can_start_and_stop_wavegen(channel: int) -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    try:
        start = service.start_wavegen(
            channel=channel,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=0.5,
            offset_v=0.0,
        )
        assert start.ok is True
        assert start.data is not None
        assert start.data["running"] is True

        capture = service.measure_analog_waveform(
            channel=channel,
            sample_rate_hz=10_000.0,
            sample_count=128,
        )
        assert capture.ok is True
        assert capture.data is not None
        assert capture.data["peak_to_peak_voltage"] > 0.1
    finally:
        stop = service.stop_wavegen(channel=channel)
        assert stop.ok is True


@pytest.mark.hardware_stand("advanced")
@pytest.mark.parametrize(
    ("output_pin", "input_pin"),
    [(output_pin, output_pin + 8) for output_pin in range(8)],
)
def test_hardware_can_write_and_read_digital_loopback(
    output_pin: int,
    input_pin: int,
) -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    try:
        low = service.write_digital_outputs(pins=[output_pin], values=[False])
        assert low.ok is True
        low_read = service.read_digital_inputs(pins=[input_pin])
        assert low_read.ok is True
        assert low_read.data is not None

        high = service.write_digital_outputs(pins=[output_pin], values=[True])
        assert high.ok is True
        high_read = service.read_digital_inputs(pins=[input_pin])
        assert high_read.ok is True
        assert high_read.data is not None

        assert low_read.data["values"][str(input_pin)] is False
        assert high_read.data["values"][str(input_pin)] is True
    finally:
        low = service.write_digital_outputs(pins=[output_pin], values=[False])
        assert low.ok is True


@pytest.mark.hardware_stand("advanced")
def test_hardware_release_preserves_digital_after_stopping_wavegen() -> None:
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
        high = service.write_digital_outputs(pins=[0], values=[True])
        assert high.ok is True
        stop = service.stop_wavegen(channel=1)
        assert stop.ok is True

        read = service.read_digital_inputs(pins=[8])

        assert read.ok is True
        assert read.data is not None
        assert read.data["values"]["8"] is True
    finally:
        released = service.release_device()
        assert released.ok is True
        assert released.data is not None
        assert released.data["digital_output_enable_mask"] == 0

    limits = service.get_digital_io_limits()
    assert limits.ok is True


@pytest.mark.hardware_stand("advanced")
def test_hardware_stopping_one_wavegen_channel_keeps_other_running() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    try:
        start_1 = service.start_wavegen(
            channel=1,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=0.5,
            offset_v=0.0,
        )
        start_2 = service.start_wavegen(
            channel=2,
            waveform="sine",
            frequency_hz=1000.0,
            amplitude_v=0.5,
            offset_v=0.0,
        )
        assert start_1.ok is True
        assert start_2.ok is True

        stop_1 = service.stop_wavegen(channel=1)
        assert stop_1.ok is True
        capture_2 = service.measure_analog_waveform(
            channel=2,
            sample_rate_hz=10_000.0,
            sample_count=128,
        )

        assert capture_2.ok is True
        assert capture_2.data is not None
        assert capture_2.data["peak_to_peak_voltage"] > 0.1
    finally:
        released = service.release_device()
        assert released.ok is True


@pytest.mark.hardware_stand("advanced")
def test_hardware_can_start_synchronized_opposite_phase_wavegen() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    try:
        start = service.start_synchronized_wavegen(
            channels=[1, 2],
            waveforms=["sine", "sine"],
            frequencies_hz=[1000.0, 1000.0],
            amplitudes_v=[2.0, 2.0],
            offsets_v=[0.0, 0.0],
            phase_degrees=[0.0, 180.0],
        )
        assert start.ok is True

        capture = service.capture_analog_waveform(
            channels=[1, 2],
            sample_rate_hz=100_000.0,
            sample_count=240,
            trigger_enabled=True,
            trigger_channel=1,
            trigger_level_v=0.0,
            trigger_edge="rising",
            trigger_hysteresis_v=0.03,
            trigger_auto_timeout_seconds=1.0,
            trigger_position_seconds=0.0002,
        )
    finally:
        released = service.release_device()
        assert released.ok is True

    assert capture.ok is True
    assert capture.data is not None
    samples_1 = [float(sample) for sample in capture.data["samples"]["1"]]
    samples_2 = [float(sample) for sample in capture.data["samples"]["2"]]
    sample_rate_hz = float(capture.data["actual_sample_rate_hz"])

    assert capture.data["triggered"] is True
    assert capture.data["auto_triggered"] is False
    assert 3.5 <= max(samples_1) - min(samples_1) <= 4.5
    assert 3.5 <= max(samples_2) - min(samples_2) <= 4.5
    assert 900.0 <= _estimate_frequency_hz(samples_1, sample_rate_hz) <= 1100.0
    assert 900.0 <= _estimate_frequency_hz(samples_2, sample_rate_hz) <= 1100.0
    assert _correlation(samples_1, samples_2) < -0.9


def _estimate_frequency_hz(samples: list[float], sample_rate_hz: float) -> float:
    crossings: list[float] = []
    for index in range(1, len(samples)):
        previous = samples[index - 1]
        current = samples[index]
        if previous < 0.0 <= current and current != previous:
            fraction = -previous / (current - previous)
            crossings.append((index - 1 + fraction) / sample_rate_hz)
    assert len(crossings) >= 2
    periods = [later - earlier for earlier, later in pairwise(crossings)]
    return 1.0 / statistics.fmean(periods)


def _correlation(left: list[float], right: list[float]) -> float:
    assert len(left) == len(right)
    left_mean = statistics.fmean(left)
    right_mean = statistics.fmean(right)
    numerator = sum((a - left_mean) * (b - right_mean) for a, b in zip(left, right, strict=True))
    denominator = math.sqrt(
        sum((a - left_mean) ** 2 for a in left) * sum((b - right_mean) ** 2 for b in right)
    )
    assert denominator > 0.0
    return numerator / denominator
