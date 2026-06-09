# Analog Discovery MCP Server

Python MCP server for Digilent Analog Discovery 2 and Analog Discovery 3.

This project exposes a small read/scope-oriented tool surface for local MCP clients:

- Detect the installed Digilent WaveForms SDK version.
- List connected WaveForms-compatible devices.
- Read one analog input voltage sample from channel 1 or 2.
- Capture analog input waveforms with optional analog edge triggers.
- Measure core voltage statistics from one analog input channel.

V1 intentionally avoids tools that drive hardware outputs such as Wavegen, power supplies, and digital output.
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
prototyping.

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

Inputs match `capture_analog_waveform` for one channel.

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

The staged development plan lives in [docs/ROADMAP.md](docs/ROADMAP.md).

## Safety

This first version does not expose output-driving instruments. Reading voltage still opens and configures the selected WaveForms device as required by the SDK.

Check wiring and input voltage limits before connecting any circuit to Analog Discovery hardware.
