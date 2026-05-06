from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


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

    @property
    def turn_count(self) -> int:
        return len(self.turns)
