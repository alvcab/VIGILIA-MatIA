from __future__ import annotations

from uuid import uuid4

from services.telephony.session import IntercomSession


class InMemorySessionFactory:
    def create(self, caller_id: str, transcript: str) -> IntercomSession:
        return IntercomSession(
            session_id=f"session-{uuid4().hex[:12]}",
            caller_id=caller_id,
            transcript=transcript,
        )
