# Analog Discovery MCP Server

Python MCP server for Digilent Analog Discovery 2 and Analog Discovery 3.

This project exposes a small, read-only first tool surface for local MCP clients:

- Detect the installed Digilent WaveForms SDK version.
- List connected WaveForms-compatible devices.
- Read one analog input voltage sample from channel 1 or 2.

V1 intentionally avoids tools that drive hardware outputs such as Wavegen, power supplies, and digital output.

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

## Development

```bash
uv sync
uv run ruff check
uv run mypy
uv run pytest
```

Hardware integration tests are skipped by default. Enable them explicitly:

```bash
AD_MCP_HARDWARE_TESTS=1 uv run pytest -m hardware
```

## Safety

This first version does not expose output-driving instruments. Reading voltage still opens and configures the selected WaveForms device as required by the SDK.

Check wiring and input voltage limits before connecting any circuit to Analog Discovery hardware.
