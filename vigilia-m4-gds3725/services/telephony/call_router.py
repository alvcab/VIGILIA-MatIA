from __future__ import annotations

from dataclasses import asdict

from services.access_control.dry_run import DryRunGate
from services.decision.policy import decide_from_text
from services.telephony.session import IntercomSession
from services.tts.canned_audio import build_spoken_response


class CallRouter:
    def route(self, session: IntercomSession) -> dict[str, object]:
        decision = decide_from_text(session.transcript)
        return {
            "mode": "session-replay",
            "session": asdict(session),
            "decision": asdict(decision),
            "spoken_response": build_spoken_response(decision),
            "gate_action": DryRunGate().handle(decision),
        }
