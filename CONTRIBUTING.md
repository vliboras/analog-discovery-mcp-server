# Contributing

Thanks for helping improve the Analog Discovery MCP Server.

## Setup

```bash
uv sync
```

## Checks

```bash
uv run ruff check
uv run mypy
uv run pytest -q
uv build
```

## Local Run

```bash
uv run analog-discovery-mcp-server
```

The server uses MCP stdio transport, so it normally runs under an MCP client.

Run with deterministic fake hardware:

```bash
AD_MCP_DWF_BACKEND=fake uv run analog-discovery-mcp-server
```

## Hardware Tests

Unit tests do not require Digilent hardware or WaveForms SDK.

Optional hardware tests are skipped unless explicitly enabled:

```bash
AD_MCP_HARDWARE_TESTS=1 uv run pytest -m hardware
```

Run a specific documented stand:

```bash
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=basic uv run pytest -m hardware -q
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=advanced uv run pytest -m hardware -q
```

## Release

Before publishing, run the checks above and inspect the sdist and wheel contents
for unintended local files or machine-specific paths.

For the first public release, publish GitHub and PyPI before adding MCP Registry
metadata:

```bash
git tag v0.2.0-alpha
uv publish
```
