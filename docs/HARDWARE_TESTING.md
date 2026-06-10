# Hardware Testing

Hardware tests use one safety gate and one broad physical stand selector.

```bash
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=basic uv run pytest -m hardware
```

`AD_MCP_HARDWARE_TESTS=1` prevents hardware tests from running accidentally.
`AD_MCP_HARDWARE_STAND` describes the assembled test bench.

## Stands

### `basic`

Requirements:

- Analog Discovery 2 or Analog Discovery 3 connected.
- Digilent WaveForms installed.
- No required signal wiring.

Used for:

- device listing
- analog input status
- small analog capture smoke tests
- core measurement smoke tests

### `analog-loopback`

Requirements:

- Includes everything from `basic`.
- W1 connected to Scope `1+`.
- GND connected to Scope `1-`.
- W1 safe to drive into Scope `1+` through the assembled loopback.
- GND connected to Scope `1-` or shared circuit ground.

Safety:

- Verify output amplitude and offset before enabling Wavegen.
- Do not connect Wavegen output to an active external source.
- Use an appropriate load or scope input and stay within Analog Discovery limits.

Used for:

- analog trigger capture validation
- Wavegen-to-scope loopback checks
- stricter waveform measurement checks

### `mixed-signal-loopback`

Requirements:

- Includes everything from `analog-loopback`.
- Adds selected digital loopbacks, to be defined when digital I/O tools are
  implemented.

Used for future:

- digital input/output checks
- logic analyzer checks
- protocol-oriented smoke tests

## Stand Selection

Broader stands satisfy narrower tests:

- `basic` runs only `basic` tests.
- `analog-loopback` runs `basic` and `analog-loopback` tests.
- `mixed-signal-loopback` runs all current hardware tests.

Examples:

```bash
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=basic uv run pytest -m hardware -q
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=analog-loopback uv run pytest -m hardware -q
```

If `AD_MCP_HARDWARE_STAND` is omitted, it defaults to `basic`.
Unknown stand names fail collection when hardware tests are enabled.
