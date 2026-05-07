from __future__ import annotations

from dataclasses import asdict, dataclass

from services.access_control.dry_run import DryRunGate
from services.decision.conversation import ConversationState, ConversationTurn, SessionMemory
from services.decision.conversation_store import ConversationStore
from services.decision.hybrid import evaluate_hybrid_decision
from services.decision.intent import extract_authorization_code, extract_intent
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
    department_authorization_status: str = ""
    registered_visit_code: str = ""


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

    def _load_previous_state(self, session_id: str) -> ConversationState | None:
        if self._conversation_store is None:
            return None
        return self._conversation_store.load(session_id)

    def _build_conversation_state(
        self,
        turn_input: TurnInput,
        next_step: str,
        spoken_response: str,
        memory: SessionMemory,
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
                memory=memory,
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
            memory=memory,
        )
        self._conversation_store.save(state)
        return state

    def _hybrid_from_decision(self, decision: Decision) -> dict[str, object]:
        return {
            "decision": asdict(decision),
            "rule_engine": {
                "applied": True,
                "reason": decision.reason,
                "confidence": decision.confidence,
            },
            "model_guidance": {
                "enabled": False,
                "prompt": "",
                "next_step": decision.next_step,
                "turn_index": decision.turn_index,
                "backend": "",
                "generated_text": "",
            },
        }

    def _resolve_department_target(
        self,
        resident_hint: str = "",
        resident_id: str = "",
        fallback: str = "",
    ) -> str:
        if self._resident_directory is not None:
            if resident_id:
                resident = self._resident_directory.get_by_id(resident_id)
                if resident is not None:
                    return resident.unit
            if resident_hint:
                resident = self._resident_directory.resolve(resident_hint) or self._resident_directory.resolve_partial(
                    resident_hint
                )
                if resident is not None:
                    return resident.unit
        return fallback

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
            department_target=self._resolve_department_target(
                resident_hint=turn_input.face_match_display_name,
                resident_id=turn_input.face_match_resident_id,
            ),
            visitor_intent="known_resident",
            next_step="complete",
            follow_up_prompt="",
            turn_index=1,
        )

    def _decision_from_department_authorization(
        self,
        turn_input: TurnInput,
        previous_memory: SessionMemory,
    ) -> Decision | None:
        status = turn_input.department_authorization_status.strip().lower()
        if not status:
            return None

        resident_hint = previous_memory.resident_candidate
        department_target = previous_memory.department_target or previous_memory.unit_candidate
        expected_code = turn_input.registered_visit_code or previous_memory.registered_visit_expected_code

        if status == "approved":
            return Decision(
                action="open",
                should_open=True,
                reason="department_authorized_access",
                confidence="high",
                resident_hint=resident_hint,
                department_target=department_target,
                visitor_intent=previous_memory.current_intent,
                next_step="complete",
            )

        if status == "denied":
            return Decision(
                action="deny_access",
                should_open=False,
                reason="department_denied_access",
                confidence="high",
                resident_hint=resident_hint,
                department_target=department_target,
                visitor_intent=previous_memory.current_intent,
                next_step="complete",
            )

        if status == "no_response":
            if expected_code:
                return Decision(
                    action="request_visit_code",
                    should_open=False,
                    reason="department_no_response_registered_visit",
                    confidence="medium",
                    resident_hint=resident_hint,
                    department_target=department_target,
                    visitor_intent=previous_memory.current_intent,
                    next_step="await_visit_code",
                )
            return Decision(
                action="deny_access",
                should_open=False,
                reason="department_no_response",
                confidence="medium",
                resident_hint=resident_hint,
                department_target=department_target,
                visitor_intent=previous_memory.current_intent,
                next_step="complete",
            )

        return None

    def _decision_from_visit_code(
        self,
        turn_input: TurnInput,
        previous_memory: SessionMemory,
    ) -> Decision | None:
        if not previous_memory.waiting_for_visit_code:
            return None

        provided_code = extract_authorization_code(turn_input.transcript)
        if not provided_code:
            return None

        expected_code = turn_input.registered_visit_code or previous_memory.registered_visit_expected_code
        if not expected_code:
            return None

        if provided_code == expected_code:
            return Decision(
                action="open",
                should_open=True,
                reason="registered_visit_code_valid",
                confidence="high",
                resident_hint=previous_memory.resident_candidate,
                department_target=previous_memory.department_target or previous_memory.unit_candidate,
                visitor_intent=previous_memory.current_intent,
                next_step="complete",
            )

        return Decision(
            action="deny_access",
            should_open=False,
            reason="registered_visit_code_invalid",
            confidence="high",
            resident_hint=previous_memory.resident_candidate,
            department_target=previous_memory.department_target or previous_memory.unit_candidate,
            visitor_intent=previous_memory.current_intent,
            next_step="complete",
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
        parts: list[str] = []
        if previous.memory.resident_candidate:
            parts.append(f"residente_candidato={previous.memory.resident_candidate}")
        if previous.memory.unit_candidate:
            parts.append(f"departamento_candidato={previous.memory.unit_candidate}")
        if previous.memory.department_target:
            parts.append(f"departamento_objetivo={previous.memory.department_target}")
        if previous.memory.current_intent and previous.memory.current_intent != "unknown":
            parts.append(f"intencion={previous.memory.current_intent}")
        if previous.memory.face_recognition_result:
            parts.append(f"rostro={previous.memory.face_recognition_result}")
        if previous.memory.department_authorization_status:
            parts.append(f"autorizacion_departamento={previous.memory.department_authorization_status}")
        if previous.memory.waiting_for_resident_confirmation:
            parts.append("esperando_confirmacion_residente=true")
        if previous.memory.waiting_for_delivery_recipient:
            parts.append("esperando_destinatario_delivery=true")
        if previous.memory.waiting_for_authorization:
            parts.append("esperando_autorizacion=true")
        if previous.memory.waiting_for_department_response:
            parts.append("esperando_respuesta_departamento=true")
        if previous.memory.waiting_for_visit_code:
            parts.append("esperando_codigo_visita=true")
        recent_turns = previous.turns[-4:]
        parts.extend(f"{turn.speaker}: {turn.text}" for turn in recent_turns if turn.text)
        return " | ".join(parts)

    def _promote_department_contact(
        self,
        decision: Decision,
        previous_memory: SessionMemory,
    ) -> Decision:
        if decision.should_open:
            return decision
        if decision.action not in {"announce_resident", "announce_delivery", "request_resident_confirmation"}:
            return decision

        department_target = decision.department_target or previous_memory.department_target
        if not department_target:
            department_target = self._resolve_department_target(
                resident_hint=decision.resident_hint,
                fallback=previous_memory.unit_candidate,
            )
        if not department_target:
            return decision

        return Decision(
            action="contact_department",
            should_open=False,
            reason="department_contact_required",
            confidence=decision.confidence,
            resident_hint=decision.resident_hint,
            department_target=department_target,
            visitor_intent=decision.visitor_intent,
            next_step="await_department_response",
            follow_up_prompt="",
            turn_index=decision.turn_index,
            face_recognition_result=decision.face_recognition_result,
        )

    def _build_session_memory(
        self,
        turn_input: TurnInput,
        decision: Decision,
    ) -> SessionMemory:
        previous_memory = SessionMemory()
        if self._conversation_store is not None:
            previous_memory = self._conversation_store.load(turn_input.session_id).memory

        intent = extract_intent(turn_input.transcript, self._resident_directory)
        resident_candidate = (
            decision.resident_hint
            or turn_input.face_match_display_name
            or turn_input.face_match_resident_id
            or previous_memory.resident_candidate
        )
        unit_candidate = intent.unit_hint or previous_memory.unit_candidate
        department_target = (
            decision.department_target
            or self._resolve_department_target(
                resident_hint=decision.resident_hint,
                resident_id=turn_input.face_match_resident_id,
                fallback=previous_memory.department_target or unit_candidate,
            )
        )
        department_authorization_status = turn_input.department_authorization_status or previous_memory.department_authorization_status
        registered_visit_expected_code = (
            turn_input.registered_visit_code or previous_memory.registered_visit_expected_code
        )

        if decision.action == "reset_interaction":
            return SessionMemory(
                current_intent=decision.visitor_intent,
                face_recognition_result=decision.face_recognition_result,
                last_next_step=decision.next_step,
            )

        if decision.reason in {"registered_visit_code_valid", "registered_visit_code_invalid"}:
            registered_visit_expected_code = ""

        if decision.reason == "department_contact_required":
            department_authorization_status = "pending"

        return SessionMemory(
            resident_candidate=resident_candidate,
            unit_candidate=unit_candidate,
            current_intent=decision.visitor_intent,
            face_recognition_result=decision.face_recognition_result or self._face_recognition_result(turn_input),
            department_target=department_target,
            department_authorization_status=department_authorization_status,
            registered_visit_expected_code=registered_visit_expected_code,
            clarification_requested=decision.next_step
            in {
                "clarify_resident",
                "clarify_resident_for_authorization",
                "clarify_authorization",
                "ask_delivery_recipient",
                "ask_resident_confirmation",
                "ask_retry",
                "await_visit_code",
            },
            waiting_for_resident_confirmation=decision.next_step == "ask_resident_confirmation",
            waiting_for_delivery_recipient=decision.next_step == "ask_delivery_recipient",
            waiting_for_authorization=decision.next_step
            in {
                "clarify_authorization",
                "clarify_resident_for_authorization",
            },
            waiting_for_department_response=decision.next_step == "await_department_response",
            waiting_for_visit_code=decision.next_step == "await_visit_code",
            last_next_step=decision.next_step,
        )

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
        previous_state = self._load_previous_state(turn_input.session_id)
        previous_memory = previous_state.memory if previous_state is not None else SessionMemory()

        decision = self._decision_from_face_match(turn_input)
        if decision is None:
            decision = self._decision_from_department_authorization(turn_input, previous_memory)

        if decision is None:
            decision = self._decision_from_visit_code(turn_input, previous_memory)

        if decision is None:
            hybrid = evaluate_hybrid_decision(
                turn_input.transcript,
                self._resident_directory,
                face_recognition_result=self._face_recognition_result(turn_input),
                conversation_summary=self._conversation_summary(turn_input.session_id),
                model_backend_name=self._model_backend_name,
                ollama_model=self._ollama_model,
                ollama_timeout_seconds=self._ollama_timeout_seconds,
            )
            decision = Decision(**hybrid["decision"])
            decision = self._promote_department_contact(decision, previous_memory)
            hybrid = self._hybrid_from_decision(decision) if decision.action == "contact_department" else hybrid
        else:
            hybrid = self._hybrid_from_decision(decision)

        decision_payload = hybrid["decision"]
        decision = Decision(**decision_payload)
        spoken_response = self._select_spoken_response(decision, hybrid["model_guidance"])
        memory = self._build_session_memory(turn_input, decision)
        conversation_state = self._build_conversation_state(
            turn_input,
            str(decision_payload.get("next_step", "start")),
            spoken_response,
            memory,
        )
        return {
            "mode": "turn-evaluation",
            "session": asdict(turn_input),
            "decision": decision_payload,
            "rule_engine": hybrid["rule_engine"],
            "model_guidance": hybrid["model_guidance"],
            "spoken_response": spoken_response,
            "gate_action": DryRunGate().handle(decision),
            "session_memory": asdict(memory),
            "conversation_state": {
                "session_id": conversation_state.session_id,
                "turn_count": conversation_state.turn_count,
                "next_step": conversation_state.next_step,
                "memory": asdict(conversation_state.memory),
                "turns": [asdict(turn) for turn in conversation_state.turns],
            },
        }
