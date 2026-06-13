---
name: Bug report
about: Report a reproducible problem with the MCP server
title: ""
labels: bug
assignees: ""
---

## Environment

- Package version or commit:
- Python version:
- Operating system:
- Analog Discovery model:
- WaveForms version:
- MCP client:
- Backend: real or fake

## Problem

Describe what happened and what you expected.

## Reproduction

List the MCP tool calls or client steps needed to reproduce the problem. Include
safe parameter values and whether hardware outputs were driven.

## Evidence

Paste relevant tool results, errors, logs, or measurements. Remove private
serial numbers if needed.

## Cleanup

Confirm whether `stop_wavegen` or `release_device` was called after any output
driving operation.
