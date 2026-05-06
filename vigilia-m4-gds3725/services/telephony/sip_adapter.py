from __future__ import annotations

import os

from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_transport import BaresipTransport
from services.telephony.sip_config import SipEndpointConfig
from services.telephony.fake_sip_transport import FakeSipTransport
from services.telephony.sip_transport import SipTransport
from services.telephony.sip_uri import build_sip_uri


class SipAdapter:
    def __init__(
        self,
        config: SipEndpointConfig | None = None,
        transport: SipTransport | None = None,
    ) -> None:
        self._config = config or SipEndpointConfig(
            device_label=os.getenv("VIGILIA_SIP_DEVICE_LABEL", "gds3725"),
            local_user=os.getenv("VIGILIA_SIP_LOCAL_USER", "vigilia"),
            local_domain=os.getenv("VIGILIA_SIP_LOCAL_DOMAIN", "127.0.0.1"),
            local_port=int(os.getenv("VIGILIA_SIP_LOCAL_PORT", "5060")),
            transport=os.getenv("VIGILIA_SIP_TRANSPORT", "udp"),
            device_user=os.getenv("VIGILIA_SIP_DEVICE_USER", "door"),
            device_domain=os.getenv("VIGILIA_SIP_DEVICE_DOMAIN", "192.168.100.20"),
            device_port=int(os.getenv("VIGILIA_SIP_DEVICE_PORT", "5060")),
        )
        self._transport = transport or FakeSipTransport()

    def _local_uri(self) -> str:
        return build_sip_uri(
            user=self._config.local_user,
            domain=self._config.local_domain,
            port=self._config.local_port,
            transport=self._config.transport,
        )

    def _device_uri(self) -> str:
        return build_sip_uri(
            user=self._config.device_user,
            domain=self._config.device_domain,
            port=self._config.device_port,
            transport=self._config.transport,
        )

    def build_preview(self, caller_id: str) -> dict[str, object]:
        local_uri = self._local_uri()
        device_uri = self._device_uri()
        return {
            "mode": "sip-preview",
            "device_label": self._config.device_label,
            "caller_id": caller_id,
            "local_endpoint": {
                "uri": local_uri,
                "user": self._config.local_user,
                "domain": self._config.local_domain,
                "port": self._config.local_port,
                "transport": self._config.transport,
            },
            "device_endpoint": {
                "uri": device_uri,
                "user": self._config.device_user,
                "domain": self._config.device_domain,
                "port": self._config.device_port,
                "transport": self._config.transport,
            },
            "session_contract": {
                "expected_audio_format": "wav/pcm16 mono",
                "expected_decision_flow": [
                    "capture_audio",
                    "transcribe",
                    "decide",
                    "respond",
                    "dry_run_or_open",
                ],
            },
        }

    def simulate_session(self, caller_id: str) -> dict[str, object]:
        local_uri = self._local_uri()
        device_uri = self._device_uri()
        registered = self._transport.register(local_uri)
        invited = self._transport.invite(
            caller_id=caller_id,
            from_uri=device_uri,
            to_uri=local_uri,
        )
        accepted = self._transport.accept(invited["call_id"])
        hung_up = self._transport.hangup(invited["call_id"])
        return {
            "mode": "sip-session",
            "device_label": self._config.device_label,
            "caller_id": caller_id,
            "local_uri": local_uri,
            "device_uri": device_uri,
            "lifecycle": [
                registered,
                invited,
                accepted,
                hung_up,
            ],
        }

    def build_baresip_preview(self, caller_id: str) -> dict[str, object]:
        local_uri = self._local_uri()
        device_uri = self._device_uri()
        baresip_config = BaresipConfig.from_env()
        transport = BaresipTransport(baresip_config)
        register_preview = transport.register(local_uri)
        return {
            "mode": "baresip-preview",
            "device_label": self._config.device_label,
            "caller_id": caller_id,
            "local_uri": local_uri,
            "device_uri": device_uri,
            "baresip": {
                "binary": baresip_config.binary,
                "config_path": baresip_config.config_path,
                "accounts_path": baresip_config.accounts_path,
                "audio_path": baresip_config.audio_path,
                "account_line": transport.build_account_line(local_uri),
                "register_preview": register_preview,
            },
            "integration_contract": {
                "incoming_call_source": device_uri,
                "local_user_agent": "baresip",
                "decision_engine": "vigilia",
            },
        }
