from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SipEndpointConfig:
    device_label: str
    local_user: str
    local_domain: str
    device_user: str = "door"
    device_domain: str = "192.168.100.20"
    device_port: int = 5060
    local_port: int = 5060
    transport: str = "udp"
