from __future__ import annotations

from services.decision.conversation_store import ConversationStore
from services.decision.resident_directory import ResidentDirectory
from services.decision.turn_evaluator import TurnEvaluator, TurnInput
from services.telephony.session import IntercomSession


class CallRouter:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        conversation_store: ConversationStore | None = None,
    ) -> None:
        self._resident_directory = resident_directory
        self._conversation_store = conversation_store

    def route(self, session: IntercomSession) -> dict[str, object]:
        result = TurnEvaluator(
            resident_directory=self._resident_directory,
            conversation_store=self._conversation_store,
        ).evaluate_turn(
            TurnInput(
                session_id=session.session_id,
                caller_id=session.caller_id,
                transcript=session.transcript,
                device_label=session.device_label,
                transport=session.transport,
            )
        )
        result["mode"] = "session-replay"
        return result
