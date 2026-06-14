# Changelog

## Unreleased

## 0.2.0 - 2026-06-13

- Document AI-assisted project development disclosure and contributor
  expectations.
- Simplify hardware test stands to `basic` and `advanced`, with advanced
  covering analog and DIO0-DIO7 to DIO8-DIO15 loopback validation.
- Add a hardware validation checkpoint to the roadmap before further Stage 4
  feature work.
- Implement Stage 3.1 custom Wavegen sample playback through `start_wavegen`.
- Add bounded custom sample validation and fake/real backend support with
  WaveForms `funcCustom` uploads.
- Implement Stage 3 basic Wavegen output tools for sine, square, triangle, and
  DC waveforms.
- Add Wavegen limit, start, stop, and status support across service, fake
  backend, real WaveForms backend, and MCP integration tests.
- Document custom repeated waveform output as the mandatory next Stage 3.1
  iteration.
- Add hardware test stand selection with documented broad bench profiles.
- Implement Stage 2 scope usability tools.
- Add analog edge trigger options to `capture_analog_waveform`.
- Add capture metadata for trigger state, sample validity, lost/corrupt counts,
  and WaveForms status time.
- Add `measure_analog_waveform` for core voltage statistics.
- Add `get_analog_input_status` for AnalogIn capability and status metadata.
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
