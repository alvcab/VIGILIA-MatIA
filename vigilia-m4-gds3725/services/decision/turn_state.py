from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TurnState:
    turn_index: int
    expects_follow_up: bool
    next_step: str
