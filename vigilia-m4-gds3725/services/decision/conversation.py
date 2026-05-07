from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class SessionMemory:
    resident_candidate: str = ""
    unit_candidate: str = ""
    current_intent: str = "unknown"
    face_recognition_result: str = ""
    department_target: str = ""
    department_authorization_status: str = ""
    registered_visit_expected_code: str = ""
    clarification_requested: bool = False
    waiting_for_resident_confirmation: bool = False
    waiting_for_delivery_recipient: bool = False
    waiting_for_authorization: bool = False
    waiting_for_department_response: bool = False
    waiting_for_visit_code: bool = False
    last_next_step: str = "start"


@dataclass(frozen=True)
class ConversationTurn:
    turn_index: int
    speaker: str
    text: str
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )


@dataclass(frozen=True)
class ConversationState:
    session_id: str
    turns: tuple[ConversationTurn, ...]
    next_step: str = "start"
    memory: SessionMemory = field(default_factory=SessionMemory)

    @property
    def turn_count(self) -> int:
        return len(self.turns)
