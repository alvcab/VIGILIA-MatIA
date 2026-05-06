from __future__ import annotations

from services.telephony.audio_ingest import LocalAudioFileIngest
from services.telephony.call_router import CallRouter
from services.telephony.sip_session_factory import SipSessionFactory
from services.transcription.service import TranscriptionService


class AudioFileFlow:
    def __init__(self) -> None:
        self._ingest = LocalAudioFileIngest()
        self._transcription = TranscriptionService()
        self._session_factory = SipSessionFactory()
        self._router = CallRouter()

    def run(self, caller_id: str, audio_file: str) -> dict[str, object]:
        capture = self._ingest.ingest(audio_file)
        transcription = self._transcription.transcribe_file(capture.source_path)
        session = self._session_factory.create(
            caller_id=caller_id,
            capture=capture,
            transcript=transcription.text,
        )
        routed = self._router.route(session)
        routed["mode"] = "audio-file"
        routed["audio_capture"] = {
            "source_path": capture.source_path,
            "format": capture.format,
            "transport": capture.transport,
        }
        routed["transcription"] = {
            "text": transcription.text,
            "source_path": transcription.source_path,
            "backend": transcription.backend,
        }
        return routed
