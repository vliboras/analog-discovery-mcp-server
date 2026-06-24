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

## AI-Assisted Contributions

AI-assisted contributions are welcome. For substantial AI-assisted changes,
disclose the tool or model used when practical in the pull request notes or
commit body.

Contributors remain responsible for understanding submitted changes, checking
license compatibility, running appropriate tests, and preserving hardware safety.

## Release

Before publishing, run the checks above and inspect the sdist and wheel contents
for unintended local files or machine-specific paths.

Configure PyPI Trusted Publishing for this repository before pushing the release
tag:

- Workflow: `.github/workflows/release.yml`
- Environment: `pypi`

The release workflow builds the sdist and wheel, checks them with Twine, runs a
minimal wheel import smoke check, creates a GitHub release with `dist/*`
attached, then publishes to PyPI through Trusted Publishing.

For the first public release, publish GitHub and PyPI before adding MCP Registry
metadata. Keep `pyproject.toml` at version `0.2.0`, then tag and push:

```bash
uv run ruff check
uv run mypy
uv run pytest -q
uv build
git tag v0.2.0
git push origin v0.2.0
uvx analog-discovery-mcp-server
```
