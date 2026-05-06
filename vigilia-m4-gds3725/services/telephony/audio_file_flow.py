from __future__ import annotations

from types import SimpleNamespace

from services.access_control.dry_run import DryRunGate
from services.decision.hybrid import evaluate_hybrid_decision
from services.decision.resident_directory import ResidentDirectory
from services.telephony.audio_ingest import LocalAudioFileIngest
from services.telephony.sip_session_factory import SipSessionFactory
from services.tts.canned_audio import build_spoken_response
from services.transcription.service import TranscriptionService


class AudioFileFlow:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        *,
        transcription_backend_name: str = "sidecar",
        whisper_model: str = "tiny",
        model_backend_name: str = "stub",
        ollama_model: str = "vigilia-mini",
        ollama_timeout_seconds: float = 8.0,
    ) -> None:
        self._ingest = LocalAudioFileIngest()
        self._transcription = TranscriptionService(
            backend_name=transcription_backend_name,
            whisper_model=whisper_model,
        )
        self._session_factory = SipSessionFactory()
        self._resident_directory = resident_directory
        self._model_backend_name = model_backend_name
        self._ollama_model = ollama_model
        self._ollama_timeout_seconds = ollama_timeout_seconds

    def run(self, caller_id: str, audio_file: str) -> dict[str, object]:
        capture = self._ingest.ingest(audio_file)
        transcription = self._transcription.transcribe_file(capture.source_path)
        session = self._session_factory.create(
            caller_id=caller_id,
            capture=capture,
            transcript=transcription.text,
        )
        hybrid = evaluate_hybrid_decision(
            transcription.text,
            self._resident_directory,
            model_backend_name=self._model_backend_name,
            ollama_model=self._ollama_model,
            ollama_timeout_seconds=self._ollama_timeout_seconds,
        )
        decision = hybrid["decision"]
        decision_obj = SimpleNamespace(
            should_open=decision["should_open"],
            reason=decision["reason"],
            action=decision["action"],
        )
        return {
            "mode": "audio-file",
            "session": {
                "session_id": session.session_id,
                "caller_id": session.caller_id,
                "transport": session.transport,
                "device_label": session.device_label,
            },
            "audio_capture": {
            "source_path": capture.source_path,
            "format": capture.format,
            "transport": capture.transport,
            },
            "transcription": {
                "text": transcription.text,
                "source_path": transcription.source_path,
                "backend": transcription.backend,
            },
            "decision": decision,
            "rule_engine": hybrid["rule_engine"],
            "model_guidance": hybrid["model_guidance"],
            "spoken_response": build_spoken_response(decision_obj),
            "gate_action": DryRunGate().handle(decision_obj),
        }
