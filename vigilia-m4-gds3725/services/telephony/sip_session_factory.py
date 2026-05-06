from __future__ import annotations

from uuid import uuid4

from services.telephony.audio_capture import AudioCapture
from services.telephony.session import IntercomSession
from services.telephony.sip_config import SipEndpointConfig


class SipSessionFactory:
    def __init__(self, config: SipEndpointConfig | None = None) -> None:
        self._config = config or SipEndpointConfig(
            device_label="gds3725",
            local_user="vigilia",
            local_domain="localhost",
        )

    def create(self, caller_id: str, capture: AudioCapture, transcript: str) -> IntercomSession:
        return IntercomSession(
            session_id=f"sip-{uuid4().hex[:12]}",
            caller_id=caller_id,
            transcript=transcript,
            audio_source_path=capture.source_path,
            transport=f"sip-{self._config.transport}",
            device_label=self._config.device_label,
        )
