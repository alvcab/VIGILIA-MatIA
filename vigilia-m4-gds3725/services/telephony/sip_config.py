from __future__ import annotations

import os
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

    @classmethod
    def from_env(cls) -> "SipEndpointConfig":
        return cls(
            device_label=os.getenv("VIGILIA_SIP_DEVICE_LABEL", "gds3725"),
            local_user=os.getenv("VIGILIA_SIP_LOCAL_USER", "vigilia"),
            local_domain=os.getenv("VIGILIA_SIP_LOCAL_DOMAIN", "127.0.0.1"),
            device_user=os.getenv("VIGILIA_SIP_DEVICE_USER", "door"),
            device_domain=os.getenv("VIGILIA_SIP_DEVICE_DOMAIN", "192.168.100.20"),
            device_port=int(os.getenv("VIGILIA_SIP_DEVICE_PORT", "5060")),
            local_port=int(os.getenv("VIGILIA_SIP_LOCAL_PORT", "5060")),
            transport=os.getenv("VIGILIA_SIP_TRANSPORT", "udp"),
        )
