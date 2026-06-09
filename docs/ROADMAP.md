# Analog Discovery MCP Server Roadmap

This file is the persistent development plan for future maintainers and coding agents.
Keep it aligned with the implemented MCP tool surface as the project moves toward a
public GitHub release.

## Current Baseline

The project is a Python MCP stdio server for Digilent Analog Discovery 2 and
Analog Discovery 3 devices through the WaveForms SDK.

Implemented MCP tools:

- `get_waveforms_version`
- `list_devices`
- `read_analog_voltage`
- `get_analog_capture_limits`
- `capture_analog_waveform`

All five tools work against the fake backend. The real WaveForms backend supports
version detection, device listing, analog voltage reads, analog capture limit
reporting, and small analog waveform captures.

## Development Stages

### Stage 1: Public Read/Capture Alpha - Closed

Ready state: the repository is public-useful for read-only Analog Discovery 2/3
workflows.

- Implement real WaveForms-backed analog capture for `capture_analog_waveform`.
- Implement real capture capability reporting for `get_analog_capture_limits`.
- Keep the existing public tool names and result shape stable.
- Preserve fake backend behavior for demos and CI.
- Add opt-in hardware tests for real capture behind `AD_MCP_HARDWARE_TESTS=1`.

### Stage 2: Scope Usability

Ready state: the MCP server is useful as a basic oscilloscope interface, not
only a raw sample fetcher.

- Extend analog capture with optional trigger configuration, acquisition
  metadata, and actual sample rate reporting.
- Add measurement-oriented tools:
  - `measure_analog_channel`
  - `get_analog_input_status`
- Keep APIs simple and JSON-friendly.
- Avoid long-lived hidden session state unless WaveForms behavior makes it
  necessary.

### Stage 3: Controlled Analog Output

Ready state: the MCP server can drive Wavegen for common lab workflows.

- Add Wavegen tools:
  - `get_wavegen_limits`
  - `start_wavegen`
  - `stop_wavegen`
  - `get_wavegen_status`
- Support basic waveform types first: sine, square, triangle, DC.
- Add custom samples only if the API remains small and predictable.
- Validate channel, frequency, amplitude, offset, duty cycle, and sample limits
  in the service layer.
- Make the fake backend simulate output state for tests.

### Stage 4: Digital I/O And Logic Analyzer

Ready state: the MCP server supports common mixed-signal workflows.

- Add digital static I/O tools:
  - `get_digital_io_limits`
  - `read_digital_inputs`
  - `write_digital_outputs`
- Add logic analyzer tools for sampled digital input capture:
  - `get_logic_analyzer_limits`
  - `capture_logic_analyzer`
- Add digital pattern output tools separately from capture:
  - `start_digital_pattern`
  - `stop_digital_pattern`
- Do not expose a public `capture_digital_waveform` tool name. Use "logic
  analyzer" terminology for sampled digital input capture to avoid confusing
  capture with digital output pattern generation.
- `capture_logic_analyzer` should return decoded per-pin samples plus
  acquisition metadata: sample rate, sample count, pins, duration, trigger
  status, and lost/corrupt sample indicators when available.
- Keep pin/channel numbering consistent with WaveForms and document the
  user-facing numbering clearly.

### Stage 5: Power, Protocols, And Release Polish

Ready state: the project is ready for broader public use and maintenance.

- Add power/system tools:
  - `get_power_supply_limits`
  - `set_power_supply`
  - `disable_power_supplies`
  - `read_system_monitor`
- Add protocol-oriented tools only after digital capture is stable:
  - `capture_uart`
  - `capture_spi`
  - `capture_i2c`
- Finish public repository polish: examples, versioned changelog entries, issue
  templates if useful, and concise safety/security notes.
- Keep safety documentation practical and minimal unless a concrete
  output-driving feature needs a direct warning.

## Documentation Roles

- `README.md`: install, quickstart, current tools, fake backend, and essential
  usage notes.
- `docs/ROADMAP.md`: staged development plan and future-agent project memory.
- `CHANGELOG.md`: release history.
- `CONTRIBUTING.md`: local development and test commands.
- `SECURITY.md`: minimal vulnerability-reporting policy.

Avoid adding more Markdown files unless they have a clear maintenance role.

## Stage 1 Implementation Notes

Status: implemented for single-acquisition analog captures. Keep these notes as
the acceptance contract for future Stage 1 maintenance.

### Public API

- Do not add new MCP tools for Stage 1.
- Keep `get_analog_capture_limits` response fields:
  - `supported_channels`
  - `default_sample_rate_hz`
  - `default_sample_count`
  - `max_sample_count_per_channel`
  - `max_total_returned_samples`
  - `device`
- Keep `capture_analog_waveform` response fields:
  - `requested_sample_rate_hz`
  - `actual_sample_rate_hz`
  - `sample_count`
  - `duration_seconds`
  - `channels`
  - `samples`
  - `device`
- Continue returning channel keys as user-facing strings such as `"1"` and
  `"2"`.

### Real Backend Behavior

- `CtypesDwfAdapter.get_analog_capture_limits` uses a short device open/close
  cycle:
  - open the selected device with `FDwfDeviceOpen`
  - query analog input channel count with `FDwfAnalogInChannelCount`
  - query sample rate bounds with `FDwfAnalogInFrequencyInfo`
  - query buffer size bounds with `FDwfAnalogInBufferSizeInfo`
  - return supported user-facing channels starting at `1`
- Use a conservative default for returned limits:
  - default sample rate: keep `1000.0`
  - default sample count: keep `1000`
  - max sample count per channel: WaveForms buffer max
  - max total returned samples: buffer max multiplied by selected supported
    channel count only if memory use stays reasonable; otherwise keep the
    current fake limit of `65_536` until larger payload handling is designed
- `CtypesDwfAdapter.capture_analog_waveform` uses single-acquisition AnalogIn
  calls:
  - open selected device and disable auto-config with `FDwfDeviceAutoConfigureSet`
  - reset/configure AnalogIn state as needed
  - enable only requested channels with `FDwfAnalogInChannelEnableSet`
  - set acquisition mode to `acqmodeSingle`
  - set requested sample rate with `FDwfAnalogInFrequencySet`
  - set requested sample count with `FDwfAnalogInBufferSizeSet`
  - start capture with `FDwfAnalogInConfigure(..., fStart=1)`
  - poll `FDwfAnalogInStatus(..., fReadData=1)` until `DwfStateDone`
  - read actual sample rate with `FDwfAnalogInFrequencyGet`
  - read each requested channel with `FDwfAnalogInStatusData`
  - always close the device in `finally`
- Add a bounded wait loop and return a clear `DwfError` on timeout instead of
  blocking indefinitely.
- Keep trigger configuration out of Stage 1; Stage 2 owns trigger behavior.
- Use double samples first; do not switch to 16-bit capture until payload size
  or performance requires it.

### Test Contract

- Add adapter-level tests with a small fake ctypes object that records
  WaveForms calls and returns deterministic sample buffers.
- Replace the current real-backend not-implemented tests with tests for:
  - limit query opens and closes the selected device
  - capture configures requested channels and sample count/rate
  - capture returns actual sample rate and per-channel samples
  - capture closes the device when an SDK call fails
  - capture timeout returns a clear `DwfError`
- Keep existing service validation tests unchanged unless the real limit fields
  require narrower assertions.
- Extend `tests/test_hardware.py` behind `AD_MCP_HARDWARE_TESTS=1` with a small
  low-sample-count capture smoke test.
- Run before completion:
  - `uv run ruff check`
  - `uv run mypy`
  - `uv run pytest`
  - optional with hardware: `AD_MCP_HARDWARE_TESTS=1 uv run pytest -m hardware`

### Done Criteria

- `AD_MCP_DWF_BACKEND=fake` behavior remains deterministic and unchanged.
- Real backend no longer returns "analog waveform capture is not implemented"
  for Stage 1 capture tools.
- No output-driving instruments are introduced.
- README no longer describes analog capture as fake-only once the real backend
  implementation and hardware smoke test are in place.

## Code Quality Rules

- Preserve the current architecture:
  - MCP wrappers in `server.py`
  - validation and result shaping in `service.py`
  - backend protocol in `adapters.py`
  - real SDK implementation in `dwf.py`
  - deterministic fake behavior in `fake.py`
  - shared payload models in `models.py`
- Every new real backend capability must have fake backend parity.
- Every new tool must have service tests, server registration/schema tests, and
  fake backend tests.
- Add MCP client integration coverage for new public tools when practical.
- Keep hardware tests opt-in with `AD_MCP_HARDWARE_TESTS=1`.
- Continue returning public tool results as `{ "ok": bool, "data": ..., "error": ... }`.

## External References

- Digilent WaveForms Reference Manual:
  <https://digilent.com/reference/software/waveforms/waveforms-3/reference-manual>
- Digilent WaveForms SDK getting started guide:
  <https://digilent.com/reference/test-and-measurement/guides/waveforms-sdk-getting-started>
