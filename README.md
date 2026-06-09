# Analog Discovery MCP Server

Python MCP server for Digilent Analog Discovery 2 and Analog Discovery 3.

This project exposes a small, read-only Stage 1 tool surface for local MCP clients:

- Detect the installed Digilent WaveForms SDK version.
- List connected WaveForms-compatible devices.
- Read one analog input voltage sample from channel 1 or 2.

V1 intentionally avoids tools that drive hardware outputs such as Wavegen, power supplies, and digital output.
Analog waveform capture is currently demo-only in the fake backend; the real WaveForms
backend does not implement capture yet.

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

### `get_waveforms_version`

Returns the detected WaveForms SDK version.

### `list_devices`

Returns connected devices with index, name, serial number, and availability.

### `read_analog_voltage`

Reads one analog input voltage sample.

Inputs:

- `channel`: `1` or `2`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

## Experimental Fake Backend Tools

These tools are available through MCP, but they are currently useful only with
`AD_MCP_DWF_BACKEND=fake`. The real WaveForms backend returns a clear "not implemented" error
until hardware-backed capture is added.

### `get_analog_capture_limits`

Returns simulated analog waveform capture limits for the selected fake device.

The fake backend reports AD3-like limits: 32,768 samples per channel and 65,536 total returned samples.

### `capture_analog_waveform`

Returns deterministic simulated analog input waveform samples.

Inputs:

- `channels`: optional list containing `1`, `2`, or both; default `[1]`
- `sample_rate_hz`: positive sample rate; default `1000.0`
- `sample_count`: samples per channel; default `1000`
- `device_index`: optional zero-based device index
- `serial_number`: optional device serial number

The server rejects requests above reported capture limits. It does not silently truncate or clamp sample arrays.

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
