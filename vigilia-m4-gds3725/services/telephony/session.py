from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone


@dataclass(frozen=True)
class IntercomSession:
    session_id: str
    caller_id: str
    transcript: str
    audio_source_path: str = ""
    transport: str = "simulated"
    device_label: str = "unknown"
    prior_turn_count: int = 0
    created_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc).isoformat(timespec="seconds")
    )
