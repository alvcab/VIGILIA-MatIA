from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from services.decision.conversation import ConversationState, ConversationTurn


class ConversationStore:
    def __init__(self, runtime_dir: str | Path) -> None:
        self._root = Path(runtime_dir) / "conversations"
        self._root.mkdir(parents=True, exist_ok=True)

    def _path_for(self, session_id: str) -> Path:
        return self._root / f"{session_id}.json"

    def load(self, session_id: str) -> ConversationState:
        path = self._path_for(session_id)
        if not path.exists():
            return ConversationState(session_id=session_id, turns=(), next_step="start")

        payload = json.loads(path.read_text(encoding="utf-8"))
        turns = tuple(ConversationTurn(**item) for item in payload.get("turns", []))
        return ConversationState(
            session_id=payload["session_id"],
            turns=turns,
            next_step=payload.get("next_step", "start"),
        )

    def save(self, state: ConversationState) -> None:
        path = self._path_for(state.session_id)
        payload = {
            "session_id": state.session_id,
            "next_step": state.next_step,
            "turns": [asdict(turn) for turn in state.turns],
        }
        path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
