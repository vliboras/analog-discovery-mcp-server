from __future__ import annotations

import pytest

from analog_discovery_mcp.backends import ENV_DWF_BACKEND, BackendConfigError, create_dwf_adapter
from analog_discovery_mcp.dwf import LazyDwfAdapter
from analog_discovery_mcp.fake import FakeDwfAdapter


def test_default_backend_is_real_lazy_adapter() -> None:
    adapter = create_dwf_adapter({})

    assert isinstance(adapter, LazyDwfAdapter)


def test_real_backend_selects_lazy_adapter() -> None:
    adapter = create_dwf_adapter({ENV_DWF_BACKEND: "real"})

    assert isinstance(adapter, LazyDwfAdapter)


def test_fake_backend_selects_fake_adapter() -> None:
    adapter = create_dwf_adapter({ENV_DWF_BACKEND: "fake"})

    assert isinstance(adapter, FakeDwfAdapter)


def test_backend_selection_is_case_insensitive() -> None:
    adapter = create_dwf_adapter({ENV_DWF_BACKEND: " FAKE "})

    assert isinstance(adapter, FakeDwfAdapter)


def test_invalid_backend_raises_clear_error() -> None:
    with pytest.raises(
        BackendConfigError,
        match="AD_MCP_DWF_BACKEND must be 'real' or 'fake', got 'demo'",
    ):
        create_dwf_adapter({ENV_DWF_BACKEND: "demo"})
