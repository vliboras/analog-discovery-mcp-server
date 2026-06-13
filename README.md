# Analog Discovery MCP Server

Python MCP server for Digilent Analog Discovery 2 and Analog Discovery 3.

This project exposes a small local instrument-control tool surface for MCP clients:

- Detect the installed Digilent WaveForms SDK version.
- List connected WaveForms-compatible devices.
- Read one analog input voltage sample from channel 1 or 2.
- Capture analog input waveforms with optional analog edge triggers.
- Measure core voltage statistics from one analog input channel.
- Drive Wavegen outputs: sine, square, triangle, DC, and bounded custom samples.
- Read and drive static digital I/O pins.
- Safely release active outputs and the WaveForms device handle.

Analog waveform capture is supported for small local captures.

## Requirements

- Python 3.11 or newer
- [uv](https://docs.astral.sh/uv/) for local development
- Digilent WaveForms installed on the machine that runs the MCP server

WaveForms includes the WaveForms SDK dynamic library used by this server:

- Windows: `dwf`
- macOS: `/Library/Frameworks/dwf.framework/dwf`
- Linux: `libdwf.so`

## Install

From a clone of this repository:

```bash
uv sync
```

Run the server locally:

```bash
uv run analog-discovery-mcp-server
```

The server uses MCP stdio transport. Your MCP client starts this process and talks to it over standard input/output; no port or web server is opened.

## Run Without Hardware

Use the fake backend to test MCP client wiring when no Analog Discovery device is connected:

```bash
AD_MCP_DWF_BACKEND=fake uv run analog-discovery-mcp-server
```

The fake backend is deterministic and for demos only. It reports one fake Analog Discovery 3 device,
fixed voltage readings for channels 1 and 2, and simulated waveform capture payloads for client
prototyping. It also simulates Wavegen output state and static digital I/O state for tests.

## MCP Client Configuration

Example local configuration:

```json
{
  "mcpServers": {
    "analog-discovery": {
      "command": "uv",
      "args": [
        "--directory",
        "/path/to/analog-discovery-mcp-server",
        "run",
        "analog-discovery-mcp-server"
      ]
    }
  }
}
```

## Device Selection

Tools can select a device using either `device_index` or `serial_number`.

You can also set defaults:

```bash
export AD_MCP_DEVICE_INDEX=0
export AD_MCP_DEVICE_SERIAL=SN:210415BD66A3
```

Set only one default at a time. Explicit tool arguments override environment defaults.

## Tools

These tools are available through MCP for both real WaveForms hardware and the fake backend.

### Device And SDK

### `get_waveforms_version`

Returns the detected WaveForms SDK version.

### `list_devices`

Returns connected devices with index, name, serial number, and availability.

### Analog Input

### `read_analog_voltage`

Reads one analog input voltage sample.

Inputs:

- `channel`: `1` or `2`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

### `get_analog_capture_limits`

Returns analog waveform capture limits for the selected device.

The fake backend reports AD3-like limits: 32,768 samples per channel and 65,536 total returned samples.
The real backend reports supported analog input channels and WaveForms buffer limits, with a conservative total returned sample limit.

### `capture_analog_waveform`

Returns analog input waveform samples for the selected channel or channels.

Inputs:

- `channels`: optional list containing `1`, `2`, or both; default `[1]`
- `sample_rate_hz`: positive sample rate; default `1000.0`
- `sample_count`: samples per channel; default `1000`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number
- `trigger_enabled`: optional analog edge trigger enable; default `false`
- `trigger_channel`: optional trigger channel; defaults to first requested channel
- `trigger_level_v`: trigger level in volts; default `0.0`
- `trigger_edge`: `rising` or `falling`; default `rising`
- `trigger_hysteresis_v`: trigger hysteresis in volts; default `0.05`
- `trigger_auto_timeout_seconds`: auto-trigger timeout; default `1.0`
- `trigger_position_seconds`: trigger position in capture window; default half duration

The server rejects requests above reported capture limits. It does not silently truncate or clamp sample arrays.

The response includes sample arrays plus metadata such as actual sample rate, trigger state,
valid sample count, lost/corrupt sample counts, and WaveForms status time when available.

### `measure_analog_waveform`

Captures one analog input channel and returns core voltage statistics without raw sample arrays.

Inputs match `capture_analog_waveform` for one channel. If a trigger is enabled,
`trigger_channel` must be the measured `channel` or omitted. To measure channel
2 while triggering from channel 1, use `capture_analog_waveform` with
`channels: [1, 2]` and compute statistics from the returned samples.

Outputs include:

- `min_voltage`
- `max_voltage`
- `mean_voltage`
- `rms_voltage`
- `peak_to_peak_voltage`
- capture metadata such as actual sample rate, duration, trigger state, and device

### `get_analog_input_status`

Returns AnalogIn capability and status metadata for the selected device.

Outputs include channel count, frequency limits, buffer limits, current frequency and buffer size,
per-channel range/offset, and current AnalogIn state when available.

### Wavegen Output

### `get_wavegen_limits`

Returns Wavegen output channels, supported waveforms, defaults, and per-channel limits.

### `start_wavegen`

Starts Wavegen output on one analog output channel.

Inputs:

- `channel`: output channel, usually `1` or `2`; default `1`
- `waveform`: `sine`, `square`, `triangle`, `dc`, or `custom`; default `sine`
- `frequency_hz`: output frequency for non-DC waveforms; default `1000.0`
- `amplitude_v`: peak amplitude for non-DC waveforms; default `1.0`
- `offset_v`: voltage offset, or DC output voltage for `dc`; default `0.0`
- `duty_cycle_percent`: symmetry/duty cycle; default `50.0`
- `samples`: normalized `custom` waveform samples, each between `-1.0` and `1.0`
- `sample_rate_hz`: playback sample rate for `custom`; required with `samples`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

For `dc`, the server uses `offset_v` as the output voltage and returns an effective
`amplitude_v` of `0.0`.

For `custom`, `samples` defines one repeated cycle. The server converts
`sample_rate_hz / len(samples)` into the WaveForms cycle frequency and validates the
sample count against `get_wavegen_limits`.

Example custom waveform:

```json
{
  "waveform": "custom",
  "samples": [-1.0, 0.0, 1.0, 0.0],
  "sample_rate_hz": 4000.0,
  "amplitude_v": 1.0,
  "offset_v": 0.0
}
```

### `start_synchronized_wavegen`

Starts multiple Wavegen output channels with hardware synchronization.

Inputs:

- `channels`: output channels; default `[1, 2]`
- `waveforms`: one waveform per channel; supports `sine`, `square`, `triangle`, and `dc`
- `frequencies_hz`: one frequency per channel; default `1000.0`
- `amplitudes_v`: one peak amplitude per channel; default `1.0`
- `offsets_v`: one voltage offset per channel; default `0.0`
- `duty_cycles_percent`: one symmetry/duty cycle per channel; default `50.0`
- `phase_degrees`: one phase per channel; default `[0.0, 180.0]` for two channels
- `master_channel`: channel that starts the synchronized group; default `1`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

All provided per-channel lists must have the same length as `channels`. The synchronized
tool uses WaveForms master/slave hardware control and phase settings; `custom` waveforms
are not supported by this tool.

Example synchronized opposite-phase sine:

```json
{
  "channels": [1, 2],
  "waveforms": ["sine", "sine"],
  "frequencies_hz": [1000.0, 1000.0],
  "amplitudes_v": [2.0, 2.0],
  "offsets_v": [0.0, 0.0],
  "phase_degrees": [0.0, 180.0],
  "master_channel": 1
}
```

### `stop_wavegen`

Stops Wavegen output on one channel. The fake backend preserves the last config in status.

### `get_wavegen_status`

Returns Wavegen state, running flag, and current config when available.

### `release_device`

Safely releases MCP ownership of the selected device. This stops active Wavegen
channels tracked by the server, disables static DIO outputs, and closes the
cached WaveForms device handle so other applications can open the hardware.

Inputs:

- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

Outputs include `released`, `wavegen_channels_stopped`,
`digital_output_enable_mask`, and `device`.

### Digital I/O

Digital pin numbers are zero-based and match WaveForms labels: public pin `0` is `DIO0`.

### `get_digital_io_limits`

Returns static digital I/O pin capabilities for the selected device.

Outputs include:

- `supported_input_pins`
- `supported_output_pins`
- `input_mask`
- `output_enable_mask`
- `device`

### `read_digital_inputs`

Reads static digital input pin values.

Inputs:

- `pins`: optional list of zero-based DIO pins; default reads all supported input pins
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

Outputs include selected `pins`, string-keyed boolean `values`, raw `input_mask`, and `device`.

### `write_digital_outputs`

Writes static digital output pin values.

Inputs:

- `pins`: list of zero-based output pins
- `values`: same-length list of booleans
- `preserve_existing`: keep unselected output state when true; default `true`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

Outputs include selected `pins`, string-keyed boolean `values`, `output_enable_mask`,
`output_mask`, and `device`.

## Development

```bash
uv sync
uv run ruff check
uv run mypy
uv run pytest
```

Test the MCP server without hardware:

```bash
AD_MCP_DWF_BACKEND=fake uv run analog-discovery-mcp-server
```

Hardware integration tests are skipped by default. Enable them explicitly:

```bash
AD_MCP_HARDWARE_TESTS=1 uv run pytest -m hardware
```

Hardware tests can also select a documented physical stand:

```bash
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=advanced uv run pytest -m hardware
```

Available stands are documented in [docs/HARDWARE_TESTING.md](docs/HARDWARE_TESTING.md).
External real MCP client/agent validation scenarios are documented in
[docs/REAL_AGENT_VALIDATION.md](docs/REAL_AGENT_VALIDATION.md).

The staged development plan lives in [docs/ROADMAP.md](docs/ROADMAP.md).

## Safety

Wavegen and digital output tools drive hardware outputs. Verify wiring, voltage range, load, and common ground before starting output.

Reading and capturing analog input still opens and configures the selected WaveForms device as required by the SDK. Check input voltage limits before connecting any circuit to Analog Discovery hardware.
