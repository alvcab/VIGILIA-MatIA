from __future__ import annotations

from dataclasses import asdict, dataclass

from services.access_control.dry_run import DryRunGate
from services.decision.conversation import ConversationState, ConversationTurn
from services.decision.conversation_store import ConversationStore
from services.decision.hybrid import evaluate_hybrid_decision
from services.decision.policy import Decision
from services.decision.resident_directory import ResidentDirectory
from services.tts.canned_audio import build_spoken_response


@dataclass(frozen=True)
class TurnInput:
    session_id: str
    caller_id: str
    transcript: str
    device_label: str = "gds3725"
    transport: str = "sip-udp"
    face_match_resident_id: str = ""
    face_match_display_name: str = ""
    face_match_confidence: str = ""
    face_match_trusted: bool = False
    face_check_performed: bool = False


class TurnEvaluator:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        conversation_store: ConversationStore | None = None,
        model_backend_name: str = "stub",
        ollama_model: str = "vigilia-mini",
        ollama_timeout_seconds: float = 8.0,
    ) -> None:
        self._resident_directory = resident_directory
        self._conversation_store = conversation_store
        self._model_backend_name = model_backend_name
        self._ollama_model = ollama_model
        self._ollama_timeout_seconds = ollama_timeout_seconds

    def _build_conversation_state(
        self,
        turn_input: TurnInput,
        next_step: str,
        spoken_response: str,
    ) -> ConversationState:
        if self._conversation_store is None:
            turns = (
                ConversationTurn(
                    turn_index=1,
                    speaker="visitor",
                    text=turn_input.transcript,
                ),
                ConversationTurn(
                    turn_index=2,
                    speaker="matia",
                    text=spoken_response,
                ),
            )
            return ConversationState(
                session_id=turn_input.session_id,
                turns=turns,
                next_step=next_step,
            )

        previous = self._conversation_store.load(turn_input.session_id)
        visitor_turn = ConversationTurn(
            turn_index=previous.turn_count + 1,
            speaker="visitor",
            text=turn_input.transcript,
        )
        assistant_turn = ConversationTurn(
            turn_index=previous.turn_count + 2,
            speaker="matia",
            text=spoken_response,
        )
        state = ConversationState(
            session_id=turn_input.session_id,
            turns=previous.turns + (visitor_turn, assistant_turn),
            next_step=next_step,
        )
        self._conversation_store.save(state)
        return state

    def _decision_from_face_match(self, turn_input: TurnInput) -> Decision | None:
        if not turn_input.face_match_trusted:
            return None

        resident_hint = turn_input.face_match_display_name or turn_input.face_match_resident_id
        if not resident_hint:
            return None

        return Decision(
            action="open",
            should_open=True,
            reason="trusted_face_match",
            confidence=turn_input.face_match_confidence or "high",
            resident_hint=resident_hint,
            visitor_intent="known_resident",
            next_step="complete",
            follow_up_prompt="",
            turn_index=1,
        )

    def _face_recognition_result(self, turn_input: TurnInput) -> str:
        if turn_input.face_match_trusted:
            return "trusted_match"
        if turn_input.face_check_performed:
            return "no_match"
        return ""

    def _conversation_summary(self, session_id: str) -> str:
        if self._conversation_store is None:
            return ""
        previous = self._conversation_store.load(session_id)
        if not previous.turns:
            return ""
        recent_turns = previous.turns[-4:]
        parts = [f"{turn.speaker}: {turn.text}" for turn in recent_turns if turn.text]
        return " | ".join(parts)

    def _select_spoken_response(
        self,
        decision: Decision,
        model_guidance: dict[str, object],
    ) -> str:
        canned = build_spoken_response(decision)
        if decision.reason == "trusted_face_match":
            return canned

        generated = str(model_guidance.get("generated_text", "")).strip()
        should_prefer_model = decision.action in {
            "clarify_authorization",
            "clarify_delivery_recipient",
            "clarify_resident",
            "request_resident_confirmation",
        }
        if should_prefer_model and generated:
            return generated
        return canned

    def evaluate_turn(self, turn_input: TurnInput) -> dict[str, object]:
        face_decision = self._decision_from_face_match(turn_input)
        if face_decision is not None:
            hybrid = {
                "decision": asdict(face_decision),
                "rule_engine": {
                    "applied": True,
                    "reason": face_decision.reason,
                    "confidence": face_decision.confidence,
                },
                "model_guidance": {
                    "enabled": False,
                    "prompt": "",
                    "next_step": face_decision.next_step,
                    "turn_index": face_decision.turn_index,
                    "backend": "",
                    "generated_text": "",
                },
            }
        else:
            hybrid = evaluate_hybrid_decision(
                turn_input.transcript,
                self._resident_directory,
                face_recognition_result=self._face_recognition_result(turn_input),
                conversation_summary=self._conversation_summary(turn_input.session_id),
                model_backend_name=self._model_backend_name,
                ollama_model=self._ollama_model,
                ollama_timeout_seconds=self._ollama_timeout_seconds,
            )
        decision_payload = hybrid["decision"]
        decision = Decision(**decision_payload)
        spoken_response = self._select_spoken_response(decision, hybrid["model_guidance"])
        conversation_state = self._build_conversation_state(
            turn_input,
            str(decision_payload.get("next_step", "start")),
            spoken_response,
        )
        return {
            "mode": "turn-evaluation",
            "session": asdict(turn_input),
            "decision": decision_payload,
            "rule_engine": hybrid["rule_engine"],
            "model_guidance": hybrid["model_guidance"],
            "spoken_response": spoken_response,
            "gate_action": DryRunGate().handle(decision),
            "conversation_state": {
                "session_id": conversation_state.session_id,
                "turn_count": conversation_state.turn_count,
                "next_step": conversation_state.next_step,
                "turns": [asdict(turn) for turn in conversation_state.turns],
            },
        }
