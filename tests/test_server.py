from __future__ import annotations

from collections.abc import Callable
from typing import Any, TypeVar, get_type_hints

from analog_discovery_mcp.models import DeviceInfo
from analog_discovery_mcp.server import create_mcp_server, register_tools
from analog_discovery_mcp.service import AnalogDiscoveryService
from tests.conftest import FakeDwfAdapter

F = TypeVar("F", bound=Callable[..., object])


class RecordingMcp:
    def __init__(self) -> None:
        self.tools: dict[str, Callable[..., object]] = {}

    def tool(
        self,
        name: str | None = None,
        title: str | None = None,
        description: str | None = None,
        annotations: object | None = None,
        icons: list[object] | None = None,
        meta: dict[str, Any] | None = None,
        structured_output: bool | None = None,
    ) -> Callable[[F], F]:
        def decorator(func: F) -> F:
            self.tools[func.__name__] = func
            return func

        return decorator


def test_registers_expected_tools() -> None:
    mcp = RecordingMcp()
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    register_tools(mcp, service)

    assert set(mcp.tools) == {
        "capture_analog_waveform",
        "get_analog_capture_limits",
        "get_analog_input_status",
        "get_waveforms_version",
        "list_devices",
        "measure_analog_waveform",
        "read_analog_voltage",
    }


def test_create_server_does_not_require_waveforms_sdk_at_startup() -> None:
    server = create_mcp_server()

    assert server.name == "Analog Discovery"


def test_create_server_uses_fake_backend_from_env(monkeypatch: Any) -> None:
    monkeypatch.setenv("AD_MCP_DWF_BACKEND", "fake")

    server = create_mcp_server()

    assert server.name == "Analog Discovery"


def test_registered_tools_call_service() -> None:
    mcp = RecordingMcp()
    adapter = FakeDwfAdapter(
        devices=[DeviceInfo(index=0, name="Analog Discovery 3", serial_number="SN:AD3")],
        read_voltage=0.75,
    )
    service = AnalogDiscoveryService(adapter, environ={})

    register_tools(mcp, service)

    version = mcp.tools["get_waveforms_version"]()
    devices = mcp.tools["list_devices"]()
    voltage = mcp.tools["read_analog_voltage"](channel=1)
    measurement = mcp.tools["measure_analog_waveform"](channel=1, sample_count=4)
    status = mcp.tools["get_analog_input_status"]()

    assert version == {"ok": True, "data": {"version": "3.24.3"}}
    assert devices == {
        "ok": True,
        "data": {
            "devices": [
                {
                    "index": 0,
                    "name": "Analog Discovery 3",
                    "serial_number": "SN:AD3",
                    "available": True,
                }
            ]
        },
    }
    assert isinstance(voltage, dict)
    assert voltage["ok"] is True
    assert voltage["data"]["voltage"] == 0.75
    assert isinstance(measurement, dict)
    assert measurement["ok"] is True
    assert measurement["data"]["mean_voltage"] == 1.0
    assert isinstance(status, dict)
    assert status["ok"] is True
    assert status["data"]["channel_count"] == 2


def test_tool_signatures_are_simple_for_mcp_schema() -> None:
    mcp = RecordingMcp()
    service = AnalogDiscoveryService(FakeDwfAdapter(), environ={})

    register_tools(mcp, service)

    annotations = get_type_hints(mcp.tools["read_analog_voltage"])
    assert annotations["channel"] is int
    assert annotations["device_index"] == int | None
    assert annotations["serial_number"] == str | None

    capture_annotations = get_type_hints(mcp.tools["capture_analog_waveform"])
    assert capture_annotations["trigger_enabled"] is bool
    assert capture_annotations["trigger_channel"] == int | None
    assert capture_annotations["trigger_edge"] is str
