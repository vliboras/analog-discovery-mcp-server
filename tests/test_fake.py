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
