from __future__ import annotations

from dataclasses import asdict

from services.access_control.dry_run import DryRunGate
from services.decision.conversation import ConversationState, ConversationTurn
from services.decision.conversation_store import ConversationStore
from services.decision.policy import decide_from_text
from services.decision.resident_directory import ResidentDirectory
from services.telephony.session import IntercomSession
from services.tts.canned_audio import build_spoken_response


class CallRouter:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        conversation_store: ConversationStore | None = None,
    ) -> None:
        self._resident_directory = resident_directory
        self._conversation_store = conversation_store

    def _build_conversation_state(self, session: IntercomSession, next_step: str) -> ConversationState:
        if self._conversation_store is None:
            turns = (
                ConversationTurn(
                    turn_index=session.prior_turn_count + 1,
                    speaker="visitor",
                    text=session.transcript,
                ),
            )
            return ConversationState(session_id=session.session_id, turns=turns, next_step=next_step)

        previous = self._conversation_store.load(session.session_id)
        new_turn = ConversationTurn(
            turn_index=previous.turn_count + 1,
            speaker="visitor",
            text=session.transcript,
        )
        state = ConversationState(
            session_id=session.session_id,
            turns=previous.turns + (new_turn,),
            next_step=next_step,
        )
        self._conversation_store.save(state)
        return state

    def route(self, session: IntercomSession) -> dict[str, object]:
        decision = decide_from_text(session.transcript, self._resident_directory)
        conversation_state = self._build_conversation_state(session, decision.next_step)
        return {
            "mode": "session-replay",
            "session": asdict(session),
            "decision": asdict(decision),
            "spoken_response": build_spoken_response(decision),
            "gate_action": DryRunGate().handle(decision),
            "conversation_state": {
                "session_id": conversation_state.session_id,
                "turn_count": conversation_state.turn_count,
                "next_step": conversation_state.next_step,
            },
        }
