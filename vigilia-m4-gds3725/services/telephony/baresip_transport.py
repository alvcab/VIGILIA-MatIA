from __future__ import annotations

from services.telephony.baresip_config import BaresipConfig
from services.telephony.sip_transport import SipTransport


class BaresipTransport(SipTransport):
    def __init__(self, config: BaresipConfig | None = None) -> None:
        self._config = config or BaresipConfig.from_env()

    def register(self, local_uri: str) -> dict[str, object]:
        return {
            "action": "register",
            "ok": True,
            "driver": "baresip",
            "command": [self._config.binary, "-f", self._config.config_path],
            "local_uri": local_uri,
        }

    def invite(self, caller_id: str, from_uri: str, to_uri: str) -> dict[str, object]:
        return {
            "action": "invite",
            "ok": True,
            "driver": "baresip",
            "caller_id": caller_id,
            "from_uri": from_uri,
            "to_uri": to_uri,
            "audio_path": self._config.audio_path,
        }

    def accept(self, call_id: str) -> dict[str, object]:
        return {
            "action": "accept",
            "ok": True,
            "driver": "baresip",
            "call_id": call_id,
        }

    def hangup(self, call_id: str) -> dict[str, object]:
        return {
            "action": "hangup",
            "ok": True,
            "driver": "baresip",
            "call_id": call_id,
        }

    def build_account_line(self, local_uri: str) -> str:
        return f"<{local_uri}>;regint=0"
