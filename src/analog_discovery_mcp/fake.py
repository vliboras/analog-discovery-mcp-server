from __future__ import annotations

from analog_discovery_mcp.dwf import DeviceInfo


class FakeDwfAdapter:
    """Deterministic runtime backend for MCP demos without hardware."""

    def __init__(self) -> None:
        self._device = DeviceInfo(
            index=0,
            name="Analog Discovery 3 (Fake)",
            serial_number="FAKE-AD3-0001",
            available=True,
        )

    def get_version(self) -> str:
        return "fake-0.1.0"

    def list_devices(self) -> list[DeviceInfo]:
        return [self._device]

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        if device_index != self._device.index:
            raise ValueError(f"No fake WaveForms device found at index {device_index}")
        if channel_index == 0:
            return 1.25
        if channel_index == 1:
            return 2.50
        raise ValueError("fake analog channel index must be 0 or 1")
