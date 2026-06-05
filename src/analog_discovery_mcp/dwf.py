from __future__ import annotations

import sys
from ctypes import (
    CDLL,
    byref,
    c_byte,
    c_double,
    c_int,
    create_string_buffer,
)
from dataclasses import dataclass
from typing import Any, Protocol, cast


class DwfError(RuntimeError):
    """Base error for WaveForms SDK access."""


class DwfUnavailableError(DwfError):
    """Raised when the WaveForms SDK dynamic library cannot be loaded."""


class DeviceOpenError(DwfError):
    """Raised when a selected WaveForms device cannot be opened."""


@dataclass(frozen=True)
class DeviceInfo:
    index: int
    name: str
    serial_number: str
    available: bool = True


class DwfAdapter(Protocol):
    def get_version(self) -> str:
        """Return the WaveForms SDK version."""

    def list_devices(self) -> list[DeviceInfo]:
        """Return connected WaveForms devices."""

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        """Read one voltage sample from zero-based analog input channel."""


def default_library_path() -> str:
    if sys.platform.startswith("win"):
        return "dwf"
    if sys.platform.startswith("darwin"):
        return "/Library/Frameworks/dwf.framework/dwf"
    return "libdwf.so"


class CtypesDwfAdapter:
    """Small ctypes wrapper around the Digilent WaveForms SDK functions used by v1."""

    def __init__(self, library_path: str | None = None) -> None:
        path = library_path or default_library_path()
        try:
            self._dwf = cast(Any, CDLL(path))
        except OSError as exc:
            raise DwfUnavailableError(f"Unable to load WaveForms SDK library: {path}") from exc

    def get_version(self) -> str:
        version = create_string_buffer(32)
        self._require_ok(self._dwf.FDwfGetVersion(version))
        return _decode_buffer(version)

    def list_devices(self) -> list[DeviceInfo]:
        count = c_int()
        self._require_ok(self._dwf.FDwfEnum(c_int(0), byref(count)))

        devices: list[DeviceInfo] = []
        for index in range(count.value):
            name = create_string_buffer(64)
            serial = create_string_buffer(64)
            available = c_byte()

            self._require_ok(self._dwf.FDwfEnumDeviceName(c_int(index), name))
            self._require_ok(self._dwf.FDwfEnumSN(c_int(index), serial))

            available_ok = self._dwf.FDwfEnumDeviceIsOpened(c_int(index), byref(available))
            is_available = bool(available_ok and not available.value)

            devices.append(
                DeviceInfo(
                    index=index,
                    name=_decode_buffer(name),
                    serial_number=_decode_buffer(serial),
                    available=is_available,
                )
            )

        return devices

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        handle = c_int()
        self._require_ok(self._dwf.FDwfDeviceOpen(c_int(device_index), byref(handle)))
        if handle.value == 0:
            raise DeviceOpenError(self._last_error_message("Unable to open WaveForms device"))

        try:
            self._require_ok(self._dwf.FDwfDeviceAutoConfigureSet(handle, c_int(0)))
            self._require_ok(
                self._dwf.FDwfAnalogInChannelEnableSet(handle, c_int(channel_index), c_int(1))
            )
            self._require_ok(self._dwf.FDwfAnalogInConfigure(handle, c_int(0), c_int(0)))
            self._require_ok(self._dwf.FDwfAnalogInStatus(handle, c_int(0), None))

            voltage = c_double()
            self._require_ok(
                self._dwf.FDwfAnalogInStatusSample(handle, c_int(channel_index), byref(voltage))
            )
            return float(voltage.value)
        finally:
            self._dwf.FDwfDeviceClose(handle)

    def _require_ok(self, result: int) -> None:
        if not result:
            raise DwfError(self._last_error_message("WaveForms SDK call failed"))

    def _last_error_message(self, fallback: str) -> str:
        message = create_string_buffer(512)
        get_last_error = getattr(self._dwf, "FDwfGetLastErrorMsg", None)
        if not callable(get_last_error):
            return fallback
        get_last_error(message)
        decoded = _decode_buffer(message)
        return decoded or fallback


def _decode_buffer(buffer: object) -> str:
    value = getattr(buffer, "value", b"")
    if isinstance(value, bytes):
        return value.decode("utf-8", errors="replace")
    return str(value)


class LazyDwfAdapter:
    """Delay WaveForms SDK loading until a tool actually needs hardware access."""

    def __init__(self, library_path: str | None = None) -> None:
        self._library_path = library_path
        self._adapter: CtypesDwfAdapter | None = None

    def get_version(self) -> str:
        return self._get_adapter().get_version()

    def list_devices(self) -> list[DeviceInfo]:
        return self._get_adapter().list_devices()

    def read_analog_voltage(self, device_index: int, channel_index: int) -> float:
        return self._get_adapter().read_analog_voltage(device_index, channel_index)

    def _get_adapter(self) -> CtypesDwfAdapter:
        if self._adapter is None:
            self._adapter = CtypesDwfAdapter(self._library_path)
        return self._adapter
