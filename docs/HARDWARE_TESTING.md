# Hardware Testing

Hardware tests use one safety gate and one physical stand selector.

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

### `advanced`

Requirements:

- Includes everything from `basic`.
- W1 connected to Scope `1+`.
- W2 connected to Scope `2+`.
- All required GND/common references connected.
- W1 safe to drive into Scope `1+` through the assembled loopback.
- W2 safe to drive into Scope `2+` through the assembled loopback.
- DIO0 connected to DIO8.
- DIO1 connected to DIO9.
- DIO2 connected to DIO10.
- DIO3 connected to DIO11.
- DIO4 connected to DIO12.
- DIO5 connected to DIO13.
- DIO6 connected to DIO14.
- DIO7 connected to DIO15.

Safety:

- Verify output amplitude and offset before enabling Wavegen.
- Verify arbitrary custom sample buffers before enabling Wavegen.
- Do not connect Wavegen output to an active external source.
- Use an appropriate load or scope input and stay within Analog Discovery limits.
- Treat DIO0-DIO7 as driven outputs and DIO8-DIO15 as observed inputs.
- Do not drive both sides of a digital loopback pair.

Used for:

- analog trigger capture validation
- Wavegen-to-scope loopback checks
- stricter waveform measurement checks
- digital input/output checks
- future logic analyzer checks
- future protocol-oriented smoke tests

Use [REAL_AGENT_VALIDATION.md](REAL_AGENT_VALIDATION.md) as the external
real-agent MCP validation contract for this stand.

## Stand Selection

Broader stands satisfy narrower tests:

- `basic` runs only `basic` tests.
- `advanced` runs all current hardware tests.

Examples:

```bash
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=basic uv run pytest -m hardware -q
AD_MCP_HARDWARE_TESTS=1 AD_MCP_HARDWARE_STAND=advanced uv run pytest -m hardware -q
```

If `AD_MCP_HARDWARE_STAND` is omitted, it defaults to `basic`.
Unknown stand names fail collection when hardware tests are enabled.
