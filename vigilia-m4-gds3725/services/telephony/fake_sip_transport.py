from __future__ import annotations

from uuid import uuid4

from services.telephony.sip_transport import SipTransport


class FakeSipTransport(SipTransport):
    def register(self, local_uri: str) -> dict[str, object]:
        return {
            "action": "register",
            "ok": True,
            "local_uri": local_uri,
        }

    def invite(self, caller_id: str, from_uri: str, to_uri: str) -> dict[str, object]:
        return {
            "action": "invite",
            "ok": True,
            "call_id": f"call-{uuid4().hex[:12]}",
            "caller_id": caller_id,
            "from_uri": from_uri,
            "to_uri": to_uri,
        }

    def accept(self, call_id: str) -> dict[str, object]:
        return {
            "action": "accept",
            "ok": True,
            "call_id": call_id,
        }

    def hangup(self, call_id: str) -> dict[str, object]:
        return {
            "action": "hangup",
            "ok": True,
            "call_id": call_id,
        }
