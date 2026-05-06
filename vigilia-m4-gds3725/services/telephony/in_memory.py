from __future__ import annotations

from uuid import uuid4

from services.telephony.session import IntercomSession


class InMemorySessionFactory:
    def create(
        self,
        caller_id: str,
        transcript: str,
        session_id: str | None = None,
        prior_turn_count: int = 0,
    ) -> IntercomSession:
        return IntercomSession(
            session_id=session_id or f"session-{uuid4().hex[:12]}",
            caller_id=caller_id,
            transcript=transcript,
            prior_turn_count=prior_turn_count,
        )
