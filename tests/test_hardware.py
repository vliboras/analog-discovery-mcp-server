from __future__ import annotations

import os

import pytest

from analog_discovery_mcp.dwf import CtypesDwfAdapter
from analog_discovery_mcp.service import AnalogDiscoveryService

pytestmark = pytest.mark.hardware


@pytest.mark.skipif(
    os.environ.get("AD_MCP_HARDWARE_TESTS") != "1",
    reason="set AD_MCP_HARDWARE_TESTS=1 to run hardware tests",
)
def test_hardware_can_list_devices() -> None:
    service = AnalogDiscoveryService(CtypesDwfAdapter())

    result = service.list_devices()

    assert result.ok is True
    assert result.data is not None
    assert "devices" in result.data
