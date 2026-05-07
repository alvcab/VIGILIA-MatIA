from __future__ import annotations

from pathlib import Path

from services.decision.conversation_store import ConversationStore
from services.decision.resident_directory import ResidentDirectory
from services.decision.turn_evaluator import TurnEvaluator, TurnInput
from services.telephony.department_authorization_runtime import DepartmentAuthorizationRuntime
from services.telephony.audio_file_flow import AudioFileFlow
from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_inbox import BaresipInbox


class BaresipPipeline:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        *,
        transcription_backend_name: str = "sidecar",
        whisper_model: str = "tiny",
        model_backend_name: str = "stub",
        ollama_model: str = "vigilia-mini",
        ollama_timeout_seconds: float = 8.0,
        baresip_config: BaresipConfig | None = None,
    ) -> None:
        self._baresip_config = baresip_config or BaresipConfig.from_env()
        self._inbox = BaresipInbox(self._baresip_config.workdir)
        self._conversation_store = ConversationStore(self._baresip_config.workdir)
        self._department_authorization = DepartmentAuthorizationRuntime(self._baresip_config.workdir)
        self._resident_directory = resident_directory
        self._model_backend_name = model_backend_name
        self._ollama_model = ollama_model
        self._ollama_timeout_seconds = ollama_timeout_seconds
        self._audio_flow = AudioFileFlow(
            resident_directory=resident_directory,
            conversation_store=self._conversation_store,
            transcription_backend_name=transcription_backend_name,
            whisper_model=whisper_model,
            model_backend_name=model_backend_name,
            ollama_model=ollama_model,
            ollama_timeout_seconds=ollama_timeout_seconds,
        )

    def _turn_evaluator(self) -> TurnEvaluator:
        return TurnEvaluator(
            resident_directory=self._resident_directory,
            conversation_store=self._conversation_store,
            model_backend_name=self._model_backend_name,
            ollama_model=self._ollama_model,
            ollama_timeout_seconds=self._ollama_timeout_seconds,
        )

    def _build_department_request(self, result: dict[str, object]) -> dict[str, object]:
        session = result["session"]
        memory = result["conversation_state"]["memory"]
        return {
            "session_id": session["session_id"],
            "caller_id": session["caller_id"],
            "device_label": session["device_label"],
            "transport": session["transport"],
            "resident_candidate": memory.get("resident_candidate", ""),
            "department_target": memory.get("department_target", ""),
            "current_intent": memory.get("current_intent", ""),
            "registered_visit_available": bool(memory.get("registered_visit_expected_code", "")),
            "request_type": "department_authorization",
        }

    def process_audio_file(
        self,
        audio_file: str,
        caller_id: str,
        metadata: dict[str, object] | None = None,
    ) -> dict[str, object]:
        resolved_metadata = (
            self._inbox.normalize_metadata(metadata) if metadata is not None else self._inbox.load_metadata(audio_file)
        )
        result = self._audio_flow.run(
            caller_id=caller_id,
            audio_file=audio_file,
            session_id=str(resolved_metadata.get("session_id", Path(audio_file).stem)),
            device_label=str(resolved_metadata.get("device_label", "gds3725")),
            transport=str(resolved_metadata.get("transport", "sip-udp")),
            face_match_resident_id=str(resolved_metadata.get("face_match_resident_id", "")),
            face_match_display_name=str(resolved_metadata.get("face_match_display_name", "")),
            face_match_confidence=str(resolved_metadata.get("face_match_confidence", "")),
            face_match_trusted=bool(resolved_metadata.get("face_match_trusted", False)),
            face_check_performed=bool(resolved_metadata.get("face_check_performed", False)),
            department_authorization_status=str(
                resolved_metadata.get("department_authorization_status", "")
            ),
            registered_visit_code=str(resolved_metadata.get("registered_visit_code", "")),
        )
        result["mode"] = "baresip-inbox"
        result["baresip_inbox"] = {
            "workdir": self._baresip_config.workdir,
            "inbox_dir": str(self._inbox.root),
            "processed_dir": str(self._inbox.processed_root),
            "metadata": resolved_metadata,
        }
        if result["decision"]["action"] == "contact_department":
            request_payload = self._build_department_request(result)
            request_path = self._department_authorization.save_request(
                session_id=str(request_payload["session_id"]),
                payload=request_payload,
            )
            result["department_authorization_request"] = {
                "request_path": str(request_path),
                "payload": request_payload,
            }
        return result

    def process_latest(self) -> dict[str, object]:
        candidates = sorted(self._inbox.root.glob("*.wav"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError("no baresip inbox wav files found")

        latest = candidates[0]
        metadata = self._inbox.load_metadata(latest)
        caller_id = str(metadata.get("caller_id", "baresip-inbox"))
        return self.process_audio_file(str(latest), caller_id=caller_id, metadata=metadata)

    def process_new_files_once(self) -> dict[str, object]:
        processed: list[dict[str, object]] = []
        skipped: list[str] = []

        candidates = sorted(self._inbox.root.glob("*.wav"), key=lambda path: path.stat().st_mtime)
        for candidate in candidates:
            if self._inbox.is_processed(candidate):
                skipped.append(str(candidate))
                continue

            metadata = self._inbox.load_metadata(candidate)
            caller_id = str(metadata.get("caller_id", "baresip-inbox"))
            result = self.process_audio_file(str(candidate), caller_id=caller_id, metadata=metadata)
            result_path = self._inbox.save_processed_result(candidate, result)
            processed.append(
                {
                    "audio_file": str(candidate),
                    "caller_id": caller_id,
                    "result_path": str(result_path),
                    "decision_action": result["decision"]["action"],
                }
            )

        return {
            "mode": "baresip-watch-once",
            "processed_count": len(processed),
            "processed": processed,
            "skipped_count": len(skipped),
            "skipped": skipped,
            "inbox_dir": str(self._inbox.root),
            "processed_dir": str(self._inbox.processed_root),
        }

    def process_department_responses_once(self) -> dict[str, object]:
        processed: list[dict[str, object]] = []
        pending = self._department_authorization.load_pending_responses()

        evaluator = self._turn_evaluator()
        for response_path, payload in pending:
            department_authorization = payload.get("department_authorization", {})
            status = ""
            if isinstance(department_authorization, dict):
                status = str(department_authorization.get("status", ""))
            if not status:
                status = str(payload.get("department_authorization_status", ""))

            session_id = str(payload.get("session_id", ""))
            caller_id = str(payload.get("caller_id", "department-authorization"))
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id=session_id,
                    caller_id=caller_id,
                    transcript="",
                    device_label=str(payload.get("device_label", "gds3725")),
                    transport=str(payload.get("transport", "sip-udp")),
                    department_authorization_status=status,
                )
            )
            processed_path = self._department_authorization.mark_response_processed(
                response_path,
                payload,
                result,
            )
            processed.append(
                {
                    "session_id": session_id,
                    "caller_id": caller_id,
                    "status": status,
                    "decision_action": result["decision"]["action"],
                    "result_path": str(processed_path),
                }
            )

        return {
            "mode": "department-watch-once",
            "processed_count": len(processed),
            "processed": processed,
            "responses_dir": str(self._department_authorization.responses_root),
            "processed_dir": str(self._department_authorization.processed_root),
        }
