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
    triggered: bool = False
    auto_triggered: bool | None = None
    valid_sample_count: int | None = None
    lost_sample_count: int | None = None
    corrupt_sample_count: int | None = None
    status_time: AnalogStatusTime | None = None
    trigger: AnalogTriggerConfig | None = None


@dataclass(frozen=True)
class AnalogTriggerConfig:
    channel: int
    level_v: float
    edge: str
    hysteresis_v: float
    auto_timeout_seconds: float
    position_seconds: float


@dataclass(frozen=True)
class AnalogStatusTime:
    seconds_utc: int
    tick: int
    ticks_per_second: int


@dataclass(frozen=True)
class AnalogInputStatus:
    channel_count: int
    frequency_min_hz: float
    frequency_max_hz: float
    current_frequency_hz: float
    buffer_size_min: int
    buffer_size_max: int
    current_buffer_size: int
    channel_ranges: dict[str, float]
    channel_offsets: dict[str, float]
    state: int | None = None


@dataclass(frozen=True)
class WavegenChannelLimits:
    frequency_min_hz: float
    frequency_max_hz: float
    amplitude_min_v: float
    amplitude_max_v: float
    offset_min_v: float
    offset_max_v: float
    duty_cycle_min_percent: float
    duty_cycle_max_percent: float
    custom_sample_count_min: int | None = None
    custom_sample_count_max: int | None = None


@dataclass(frozen=True)
class WavegenLimits:
    supported_channels: list[int]
    supported_waveforms: list[str]
    default_waveform: str
    default_frequency_hz: float
    default_amplitude_v: float
    default_offset_v: float
    default_duty_cycle_percent: float
    channel_limits: dict[str, WavegenChannelLimits]


@dataclass(frozen=True)
class WavegenConfig:
    channel: int
    waveform: str
    frequency_hz: float
    amplitude_v: float
    offset_v: float
    duty_cycle_percent: float
    samples: list[float] | None = None
    sample_rate_hz: float | None = None


@dataclass(frozen=True)
class WavegenStatus:
    channel: int
    state: int | None
    running: bool
    config: WavegenConfig | None = None


class ToolResult(BaseModel):
    ok: bool
    data: dict[str, Any] | None = None
    error: str | None = None
