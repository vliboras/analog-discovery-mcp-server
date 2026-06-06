from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from pydantic import BaseModel


@dataclass(frozen=True)
class DeviceInfo:
    index: int
    name: str
    serial_number: str
    available: bool = True


@dataclass(frozen=True)
class AnalogCaptureLimits:
    supported_channels: list[int]
    default_sample_rate_hz: float
    default_sample_count: int
    max_sample_count_per_channel: int
    max_total_returned_samples: int


@dataclass(frozen=True)
class AnalogCapture:
    sample_rate_hz: float
    sample_count: int
    channels: list[int]
    samples: dict[str, list[float]]


class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
