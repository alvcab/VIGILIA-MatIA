from __future__ import annotations

from services.decision.conversation_store import ConversationStore
from services.decision.resident_directory import ResidentDirectory
from services.decision.turn_evaluator import TurnEvaluator, TurnInput
from services.telephony.audio_ingest import LocalAudioFileIngest
from services.telephony.sip_session_factory import SipSessionFactory
from services.transcription.service import TranscriptionService


class AudioFileFlow:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        conversation_store: ConversationStore | None = None,
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
        self._conversation_store = conversation_store
        self._model_backend_name = model_backend_name
        self._ollama_model = ollama_model
        self._ollama_timeout_seconds = ollama_timeout_seconds

    def run(
        self,
        caller_id: str,
        audio_file: str,
        *,
        session_id: str = "",
        device_label: str = "unknown",
        transport: str = "simulated",
        face_match_resident_id: str = "",
        face_match_display_name: str = "",
        face_match_confidence: str = "",
        face_match_trusted: bool = False,
        face_check_performed: bool = False,
        department_authorization_status: str = "",
        registered_visit_code: str = "",
    ) -> dict[str, object]:
        capture = self._ingest.ingest(audio_file)
        transcription = self._transcription.transcribe_file(capture.source_path)
        session = self._session_factory.create(
            caller_id=caller_id,
            capture=capture,
            transcript=transcription.text,
        )
        if session_id:
            session = type(session)(
                session_id=session_id,
                caller_id=session.caller_id,
                transcript=session.transcript,
                audio_source_path=session.audio_source_path,
                transport=transport,
                device_label=device_label,
                prior_turn_count=session.prior_turn_count,
                created_at=session.created_at,
            )
        evaluator_result = TurnEvaluator(
            self._resident_directory,
            conversation_store=self._conversation_store,
            model_backend_name=self._model_backend_name,
            ollama_model=self._ollama_model,
            ollama_timeout_seconds=self._ollama_timeout_seconds,
        ).evaluate_turn(
            TurnInput(
                session_id=session.session_id,
                caller_id=session.caller_id,
                transcript=transcription.text,
                device_label=device_label if device_label != "unknown" else session.device_label,
                transport=transport if transport != "simulated" else session.transport,
                face_match_resident_id=face_match_resident_id,
                face_match_display_name=face_match_display_name,
                face_match_confidence=face_match_confidence,
                face_match_trusted=face_match_trusted,
                face_check_performed=face_check_performed,
                department_authorization_status=department_authorization_status,
                registered_visit_code=registered_visit_code,
            )
        )
        return {
            "mode": "audio-file",
            "session": evaluator_result["session"],
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
            "decision": evaluator_result["decision"],
            "rule_engine": evaluator_result["rule_engine"],
            "model_guidance": evaluator_result["model_guidance"],
            "spoken_response": evaluator_result["spoken_response"],
            "gate_action": evaluator_result["gate_action"],
            "conversation_state": evaluator_result["conversation_state"],
        }
