from __future__ import annotations

import pytest

from analog_discovery_mcp.dwf import DeviceInfo, DwfAdapter, DwfError


class FakeDwfAdapter(DwfAdapter):
    def __init__(
        self,
        devices: list[DeviceInfo] | None = None,
        version: str = "3.24.3",
        read_voltage: float = 1.25,
        fail_version: Exception | None = None,
        fail_list: Exception | None = None,
        fail_read: Exception | None = None,
    ) -> None:
        self.devices = devices or []
        self.version = version
        self.read_voltage_value = read_voltage
        self.fail_version = fail_version
        self.fail_list = fail_list
        self.fail_read = fail_read
        self.read_calls: list[tuple[int, int]] = []

    def get_version(self) -> str:
        if self.fail_version:
            raise self.fail_version
        return self.version

    def list_devices(self) -> list[DeviceInfo]:
        if self.fail_list:
            raise self.fail_list
        return self.devices

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        self.read_calls.append((device_index, channel_index))
        if self.fail_read:
            raise self.fail_read
        return self.read_voltage_value


@pytest.fixture
def sample_devices() -> list[DeviceInfo]:
    return [
        DeviceInfo(index=0, name="Analog Discovery 2", serial_number="SN:AD2"),
        DeviceInfo(index=1, name="Analog Discovery 3", serial_number="SN:AD3"),
    ]


@pytest.fixture
def sdk_missing_error() -> DwfError:
    return DwfError("Unable to load WaveForms SDK library: libdwf.so")
