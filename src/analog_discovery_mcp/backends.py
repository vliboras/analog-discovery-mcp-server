from __future__ import annotations

import os
from collections.abc import Mapping

from analog_discovery_mcp.adapters import DwfAdapter
from analog_discovery_mcp.dwf import LazyDwfAdapter
from analog_discovery_mcp.fake import FakeDwfAdapter

ENV_DWF_BACKEND = "AD_MCP_DWF_BACKEND"


class BackendConfigError(ValueError):
    """Raised when backend configuration is invalid."""


def create_dwf_adapter(environ: Mapping[str, str] | None = None) -> DwfAdapter:
    env = os.environ if environ is None else environ
    backend = env.get(ENV_DWF_BACKEND, "real").strip().lower()

    if backend == "real":
        return LazyDwfAdapter()
    if backend == "fake":
        return FakeDwfAdapter()

    raise BackendConfigError(f"{ENV_DWF_BACKEND} must be 'real' or 'fake', got {backend!r}")
