# Real MCP Agent Validation

## Release Status

For the `0.2.0` public alpha release, maintainers completed the external real
MCP client/agent validation checkpoint against the `advanced` hardware stand.
The scenarios below remain the validation contract for future release checks.

This document defines an external, supervised validation contract for checking
how an independent MCP client/agent uses `analog-discovery-mcp-server` with real
Analog Discovery hardware.

It is not an automated pytest replacement and it is not a script recipe. The
agent should discover the available MCP tools from the server, inspect schemas
and tool results, choose safe parameters from reported limits, recover from
errors, clean up outputs, and report whether the server surface is clear and
complete.

## Hardware Contract

Use the `advanced` hardware stand:

- W1 connected to Scope `1+`.
- W2 connected to Scope `2+`.
- Common GND references connected.
- DIO0-DIO7 looped to DIO8-DIO15 respectively.
- Real WaveForms backend. Do not use the fake backend for this validation.

Before driving outputs:

- Verify wiring and common ground.
- Verify output amplitude and offset before enabling Wavegen.
- Do not connect Wavegen outputs to active external sources.
- Treat DIO0-DIO7 as driven outputs and DIO8-DIO15 as observed inputs.
- End every output-driving task by stopping outputs or releasing the device.

## Agent Contract

Run each scenario in a fresh or clearly reset agent context. Give the agent only
the scenario text and access to the MCP server. Do not prescribe exact MCP calls
or local shell commands; the point is to observe how the agent uses the tool
surface returned by MCP.

For each scenario, record:

- MCP client/agent identity.
- Device serial number.
- Scenario text.
- MCP tools selected by the agent and key arguments.
- Tool results, including `ok=false` errors.
- Whether parameters were chosen from reported limits.
- Whether cleanup was performed.
- Numeric evidence and plots where useful.
- Conclusion: `pass`, `degraded`, `server bug`, `docs gap`, `missing capability`,
  or `agent error`.

Generated reports and plots should be stored outside this repository unless a
maintainer explicitly decides to add a curated result.

## Scenarios

### 1. Discovery And Readiness

Using the MCP server, verify that WaveForms is available, list connected
devices, choose the first available Analog Discovery device, and report analog
input limits, Wavegen limits, and digital I/O limits. Do not drive outputs.

Expected evidence:

- Selected device name, index, serial number, and availability.
- Supported analog input channels and sample limits.
- Wavegen channels, supported waveforms, amplitude/offset/frequency limits, and
  phase limits when reported.
- Supported DIO pins and masks.

### 2. Basic Analog Capture

Capture a quiet baseline from Scope channel 1 and Scope channel 2 for about
10 ms at a reasonable sample rate. Summarize min, max, mean, RMS, and whether
the data looks idle or noisy.

Expected evidence:

- Both channels measured or captured.
- Sample rate and sample count respect reported limits.
- Values are reported with units.
- The agent does not invent unavailable metadata.
- If measuring one channel while triggering from another channel is needed, the
  agent should use a multi-channel capture and compute statistics from the
  returned samples; single-channel measurement only triggers on the measured
  channel.

### 3. Single-Channel Wavegen-To-Scope Trigger

Generate a 1 kHz sine on W1 with 1 V peak amplitude and 0 V offset. Capture
about two periods on Scope channel 1 using an analog rising-edge trigger near
0 V. Report actual sample rate, trigger status, peak-to-peak voltage, and a
frequency estimate.

Expected evidence:

- W1 output started with safe amplitude and offset.
- Trigger result distinguishes real trigger from auto-trigger when metadata is
  available.
- Captured signal is roughly 2 V peak-to-peak and roughly 1 kHz.
- Output is stopped or the device is released.

### 4. Synchronized Opposite-Phase Wavegen

Using the advanced stand, generate synchronized sine waves on W1 and W2 with
180 degree phase difference and 2 V peak amplitude. Capture about two periods of
both signals with an analog trigger. Prepare a two-trace plot and decide whether
the synchronized Wavegen feature works well.

Expected evidence:

- The agent discovers and uses the synchronized Wavegen tool instead of manually
  approximating phase with unrelated operations.
- The requested relationship is W1/W2 at the same frequency with opposite phase.
- Both captured signals are roughly 4 V peak-to-peak and roughly 1 kHz.
- The plot and numeric evidence show strong opposite-phase alignment.
- Output cleanup is performed.

### 5. Wavegen Independence And Cleanup

Start W1 as a 500 Hz square wave at 0.5 V peak amplitude and W2 as a 750 Hz
triangle wave at 0.5 V peak amplitude. Verify from scope measurements that both
are present. Stop only W1, confirm W2 is still running, then safely release the
device.

Expected evidence:

- Both Wavegen channels are used.
- Scope data or measurements show both outputs before stopping W1.
- W1 stop does not stop W2.
- Final release leaves no active outputs.

### 6. Custom Waveform Validation

Create a bounded repeated custom waveform on W1 that approximates one sine
cycle, output it at 250 Hz with 1 V peak amplitude, capture two cycles on Scope
channel 1, and compare the captured shape with the intended custom samples.

Expected evidence:

- Custom sample limits are checked.
- Custom samples are normalized and bounded.
- The agent understands that output frequency is derived from sample playback
  rate divided by custom sample count.
- Captured shape, frequency, and amplitude are summarized.
- Output cleanup is performed.

### 7. Digital Loopback

Using the advanced DIO loopback, drive DIO0-DIO7 with pattern `10101010`, read
DIO8-DIO15, then drive `01010101` and read again. Report mismatches and leave
driven DIO outputs low or released.

Expected evidence:

- DIO numbering is zero-based.
- Only DIO0-DIO7 are driven.
- DIO8-DIO15 are read.
- Mapped loopback pairs DIO0->DIO8 through DIO7->DIO15 are compared.
- Cleanup leaves driven outputs low or disabled.

### 8. Negative/Safety Behavior

Request an obviously invalid operation safely, such as capturing more samples
than the reported maximum. Then recover with a valid request. Explain the server
error and the corrected request.

Expected evidence:

- The invalid request is based on discovered limits.
- The agent handles `ok=false` without crashing.
- A corrected request succeeds.
- No unnecessary outputs are driven.

## Fix Decision Rules

Fix the MCP server only when evidence points to server behavior, not agent
reasoning.

- `server bug`: a valid request returns wrong data, bad metadata, unsafe stale
  state, failed cleanup, broken trigger reporting, incorrect DIO mapping, or
  inconsistent real/fake behavior.
- `docs gap`: the agent repeatedly misuses a tool because schema docs or project
  docs omit a critical constraint.
- `missing capability`: a reasonable hardware task cannot be expressed with the
  current API.
- `agent error`: the server response was correct, but the agent selected unsafe
  parameters, ignored limits, invented fields, or failed cleanup.
- `degraded`: the task completed, but with weak evidence or manual intervention.

Do not add Stage 4 logic analyzer or digital pattern features during this
checkpoint unless validation exposes a direct Stage 4A safety or correctness
dependency.

## Assumptions

- The MCP client can expose tool names, schemas, and structured results to the
  agent.
- Plotting is an agent/client responsibility because the MCP server returns
  samples but no plot-generation tool.
- "2 V amplitude" means Wavegen peak amplitude, so the expected sine is roughly
  4 V peak-to-peak.
- Synchronized Wavegen v1 is start/restart synchronization, not gapless live
  frequency sweeping.
