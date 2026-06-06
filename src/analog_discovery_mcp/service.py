from __future__ import annotations

import os
from collections.abc import Mapping
from dataclasses import asdict
from typing import Any

from pydantic import BaseModel, Field

from analog_discovery_mcp.dwf import AnalogCaptureLimits, DeviceInfo, DwfAdapter, DwfError

ENV_DEVICE_INDEX = "AD_MCP_DEVICE_INDEX"
ENV_DEVICE_SERIAL = "AD_MCP_DEVICE_SERIAL"
DEFAULT_CAPTURE_CHANNELS = [1]
DEFAULT_CAPTURE_SAMPLE_RATE_HZ = 1000.0
DEFAULT_CAPTURE_SAMPLE_COUNT = 1000


class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None


class AnalogDiscoveryService:
    def __init__(self, adapter: DwfAdapter, environ: Mapping[str, str] | None = None) -> None:
        self._adapter = adapter
        self._environ = os.environ if environ is None else environ

    def get_waveforms_version(self) -> ToolResult:
        try:
            return ToolResult(ok=True, data={"version": self._adapter.get_version()})
        except DwfError as exc:
            return ToolResult(ok=False, error=str(exc))

    def list_devices(self) -> ToolResult:
        try:
            devices = [asdict(device) for device in self._adapter.list_devices()]
            return ToolResult(ok=True, data={"devices": devices})
        except DwfError as exc:
            return ToolResult(ok=False, error=str(exc))

    def read_analog_voltage(
        self,
        channel: int,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        if channel not in (1, 2):
            return ToolResult(ok=False, error="channel must be 1 or 2")

        try:
            selected_device = self._select_device(device_index, serial_number)
            voltage = self._adapter.read_analog_voltage(
                device_index=selected_device.index,
                channel_index=channel - 1,
            )
            return ToolResult(
                ok=True,
                data={
                    "voltage": voltage,
                    "unit": "V",
                    "channel": channel,
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def get_analog_capture_limits(
        self,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_analog_capture_limits(selected_device.index)
            return ToolResult(
                ok=True,
                data={
                    **asdict(limits),
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def capture_analog_waveform(
        self,
        channels: list[int] | None = None,
        sample_rate_hz: float = DEFAULT_CAPTURE_SAMPLE_RATE_HZ,
        sample_count: int = DEFAULT_CAPTURE_SAMPLE_COUNT,
        device_index: int | None = None,
        serial_number: str | None = None,
    ) -> ToolResult:
        requested_channels = DEFAULT_CAPTURE_CHANNELS if channels is None else channels

        try:
            selected_device = self._select_device(device_index, serial_number)
            limits = self._adapter.get_analog_capture_limits(selected_device.index)
            self._validate_capture_request(
                requested_channels,
                sample_rate_hz,
                sample_count,
                limits,
            )
            capture = self._adapter.capture_analog_waveform(
                device_index=selected_device.index,
                channel_indices=[channel - 1 for channel in requested_channels],
                sample_rate_hz=sample_rate_hz,
                sample_count=sample_count,
            )
            return ToolResult(
                ok=True,
                data={
                    "requested_sample_rate_hz": sample_rate_hz,
                    "actual_sample_rate_hz": capture.sample_rate_hz,
                    "sample_count": capture.sample_count,
                    "duration_seconds": capture.sample_count / capture.sample_rate_hz,
                    "channels": capture.channels,
                    "samples": capture.samples,
                    "device": asdict(selected_device),
                },
            )
        except (DwfError, ValueError) as exc:
            return ToolResult(ok=False, error=str(exc))

    def _select_device(
        self,
        device_index: int | None,
        serial_number: str | None,
    ) -> DeviceInfo:
        requested_index, requested_serial = self._resolve_selection(device_index, serial_number)
        devices = self._adapter.list_devices()

        if not devices:
            raise ValueError("No WaveForms devices found")

        if requested_serial is not None:
            for device in devices:
                if device.serial_number == requested_serial:
                    return device
            raise ValueError(f"No WaveForms device found with serial number {requested_serial!r}")

        if requested_index is None:
            requested_index = 0

        for device in devices:
            if device.index == requested_index:
                return device

        raise ValueError(f"No WaveForms device found at index {requested_index}")

    def _resolve_selection(
        self,
        device_index: int | None,
        serial_number: str | None,
    ) -> tuple[int | None, str | None]:
        if device_index is not None and serial_number:
            raise ValueError("Use either device_index or serial_number, not both")

        env_index = self._environ.get(ENV_DEVICE_INDEX)
        env_serial = self._environ.get(ENV_DEVICE_SERIAL)

        if device_index is not None or serial_number:
            return device_index, serial_number

        if env_index and env_serial:
            raise ValueError(f"Set only one of {ENV_DEVICE_INDEX} or {ENV_DEVICE_SERIAL}")

        if env_serial:
            return None, env_serial

        if env_index:
            try:
                return int(env_index), None
            except ValueError as exc:
                raise ValueError(f"{ENV_DEVICE_INDEX} must be an integer") from exc

        return None, None

    def _validate_capture_request(
        self,
        channels: list[int],
        sample_rate_hz: float,
        sample_count: int,
        limits: AnalogCaptureLimits,
    ) -> None:
        if not channels:
            raise ValueError("channels must not be empty")

        if len(set(channels)) != len(channels):
            raise ValueError("channels must not contain duplicates")

        unsupported_channels = sorted(set(channels) - set(limits.supported_channels))
        if unsupported_channels:
            raise ValueError(
                "channels must only contain supported channels "
                f"{limits.supported_channels}; got {unsupported_channels}"
            )

        if sample_rate_hz <= 0:
            raise ValueError("sample_rate_hz must be positive")

        if sample_count < 1 or sample_count > limits.max_sample_count_per_channel:
            raise ValueError(
                "sample_count must be between 1 and "
                f"{limits.max_sample_count_per_channel}"
            )

        total_samples = len(channels) * sample_count
        if total_samples > limits.max_total_returned_samples:
            raise ValueError(
                "total returned samples must be at most "
                f"{limits.max_total_returned_samples}"
            )


class ReadAnalogVoltageInput(BaseModel):
    channel: int = Field(description="Analog input channel, 1 or 2")
    device_index: int | None = Field(default=None, description="Optional zero-based device index")
    serial_number: str | None = Field(default=None, description="Optional device serial number")
