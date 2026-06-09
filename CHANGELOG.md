# Changelog

## Unreleased

- Complete Stage 1 public read/capture alpha.
- Implement real WaveForms-backed analog waveform capture with bounded polling,
  actual sample rate reporting, and per-channel sample payloads.
- Add real analog capture limit reporting from WaveForms channel and buffer
  capability queries.
- Add adapter-level tests for real capture SDK call flow, failure cleanup, and
  timeout handling.
- Add opt-in hardware smoke coverage for small analog waveform captures.
- Refactor adapter protocol and shared models into separate modules.
- Add experimental fake-backed analog waveform capture tools.
- Add fake analog capture limit reporting.
- Add deterministic fake backend for MCP demos without hardware.
- Add `AD_MCP_DWF_BACKEND` backend selection.
- Document fake backend usage.

## 0.1.0 - 2026-06-06

- Add initial MCP server for Analog Discovery 2/3.
- Add WaveForms SDK adapter with lazy loading.
- Add tools for SDK version, device listing, and analog voltage reads.
- Add tests, packaging, and public repository docs.
