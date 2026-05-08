from __future__ import annotations

import json
import shutil
from dataclasses import dataclass
from pathlib import Path

from services.transcription.service import TranscriptionService
from services.telephony.baresip_pipeline import BaresipPipeline


@dataclass(frozen=True)
class MatiaCallServiceRuntime:
    root: Path
    requests_root: Path
    active_root: Path
    completed_root: Path
    reply_audio_inbox_root: Path
    reply_audio_processed_root: Path

    @classmethod
    def from_workdir(cls, workdir: str | Path) -> "MatiaCallServiceRuntime":
        root = Path(workdir) / "matia_call_service"
        requests_root = root / "requests"
        active_root = root / "active"
        completed_root = root / "completed"
        reply_audio_inbox_root = root / "reply_audio_inbox"
        reply_audio_processed_root = root / "reply_audio_processed"
        requests_root.mkdir(parents=True, exist_ok=True)
        active_root.mkdir(parents=True, exist_ok=True)
        completed_root.mkdir(parents=True, exist_ok=True)
        reply_audio_inbox_root.mkdir(parents=True, exist_ok=True)
        reply_audio_processed_root.mkdir(parents=True, exist_ok=True)
        return cls(
            root=root,
            requests_root=requests_root,
            active_root=active_root,
            completed_root=completed_root,
            reply_audio_inbox_root=reply_audio_inbox_root,
            reply_audio_processed_root=reply_audio_processed_root,
        )

    def request_path(self, session_id: str) -> Path:
        return self.requests_root / f"{session_id}.request.json"

    def active_path(self, session_id: str) -> Path:
        return self.active_root / f"{session_id}.active.json"

    def completed_path(self, session_id: str) -> Path:
        return self.completed_root / f"{session_id}.completed.json"

    def reply_audio_inbox_path(self, session_id: str, suffix: str = ".wav") -> Path:
        return self.reply_audio_inbox_root / f"{session_id}{suffix}"

    def reply_audio_result_path(self, session_id: str) -> Path:
        return self.reply_audio_processed_root / f"{session_id}.reply-audio.result.json"

    def save_active(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.active_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def save_request(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.request_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def save_completed(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.completed_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def load_request(self, session_id: str) -> dict[str, object] | None:
        request = self.request_path(session_id)
        if request.exists():
            return json.loads(request.read_text(encoding="utf-8"))
        return None

    def list_pending_requests(self) -> list[dict[str, object]]:
        items: list[dict[str, object]] = []
        for request_path in sorted(self.requests_root.glob("*.request.json"), key=lambda path: path.stat().st_mtime):
            items.append(json.loads(request_path.read_text(encoding="utf-8")))
        return items

    def list_pending_reply_audio_files(self) -> list[Path]:
        return sorted(
            self.reply_audio_inbox_root.glob("*.wav"),
            key=lambda path: path.stat().st_mtime,
        )

    def load_status(self, session_id: str) -> dict[str, object] | None:
        active = self.active_path(session_id)
        if active.exists():
            return json.loads(active.read_text(encoding="utf-8"))
        completed = self.completed_path(session_id)
        if completed.exists():
            return json.loads(completed.read_text(encoding="utf-8"))
        return None

    def mark_request_started(self, session_id: str) -> None:
        self.request_path(session_id).unlink(missing_ok=True)


class MatiaDepartmentCallService:
    def __init__(
        self,
        pipeline: BaresipPipeline,
        runtime: MatiaCallServiceRuntime,
        transcription_service: TranscriptionService | None = None,
    ) -> None:
        self._pipeline = pipeline
        self._runtime = runtime
        self._transcription_service = transcription_service or TranscriptionService()

    def start_call(
        self,
        request_payload: dict[str, object],
        call_plan: dict[str, object],
        *,
        dry_run: bool = True,
    ) -> dict[str, object]:
        result = self._pipeline.start_department_call_session(
            request_payload,
            call_plan,
            dry_run=dry_run,
        )
        session_id = str(result["call_session"]["session_id"])
        snapshot = {
            "service": "matia_department_call_service",
            "state": "active",
            "dry_run": dry_run,
            "start_result": result,
        }
        self._runtime.save_active(session_id, snapshot)
        return snapshot

    def enqueue_call(
        self,
        request_payload: dict[str, object],
        call_plan: dict[str, object],
        *,
        dry_run: bool = True,
    ) -> dict[str, object]:
        session_id = str(request_payload.get("session_id", ""))
        payload = {
            "service": "matia_department_call_service",
            "state": "queued",
            "dry_run": dry_run,
            "request_payload": request_payload,
            "call_plan": call_plan,
        }
        request_path = self._runtime.save_request(session_id, payload)
        return {
            "service": "matia_department_call_service",
            "state": "queued",
            "request_path": str(request_path),
            "request": payload,
        }

    def run_once(self) -> dict[str, object]:
        pending = self._runtime.list_pending_requests()
        if not pending:
            return {
                "service": "matia_department_call_service",
                "mode": "run-once",
                "processed_count": 0,
                "processed": [],
            }

        processed: list[dict[str, object]] = []
        for item in pending:
            request_payload = dict(item.get("request_payload", {}))
            call_plan = dict(item.get("call_plan", {}))
            dry_run = bool(item.get("dry_run", True))
            started = self.start_call(
                request_payload=request_payload,
                call_plan=call_plan,
                dry_run=dry_run,
            )
            session_id = str(request_payload.get("session_id", ""))
            self._runtime.mark_request_started(session_id)
            processed.append(started)

        return {
            "service": "matia_department_call_service",
            "mode": "run-once",
            "processed_count": len(processed),
            "processed": processed,
        }

    def finish_call(
        self,
        session_id: str,
        *,
        timeout_seconds: float = 5.0,
    ) -> dict[str, object]:
        prior = self._runtime.load_status(session_id) or {}
        result = self._pipeline.finish_department_call_session(
            session_id,
            timeout_seconds=timeout_seconds,
        )
        snapshot = {
            "service": "matia_department_call_service",
            "state": "completed",
            "prior_status": prior,
            "finish_result": result,
        }
        self._runtime.save_completed(session_id, snapshot)
        self._runtime.active_path(session_id).unlink(missing_ok=True)
        return snapshot

    def get_status(self, session_id: str) -> dict[str, object] | None:
        return self._runtime.load_status(session_id)

    def interpret_department_reply(self, transcript: str) -> dict[str, str]:
        normalized = " ".join(transcript.strip().lower().split())
        if not normalized:
            return {"status": "no_response", "reason": "empty_reply"}

        approved_markers = (
            "si",
            "sí",
            "autorizo",
            "autorizado",
            "puede pasar",
            "que pase",
            "dale acceso",
            "permito el ingreso",
        )
        denied_markers = (
            "no",
            "no autorizo",
            "no autorizado",
            "rechazo",
            "no puede pasar",
            "niego el ingreso",
            "denegado",
        )

        if any(marker in normalized for marker in denied_markers):
            return {"status": "denied", "reason": "matched_denial_marker"}
        if any(marker in normalized for marker in approved_markers):
            return {"status": "approved", "reason": "matched_approval_marker"}
        return {"status": "unknown", "reason": "no_status_marker_detected"}

    def submit_department_reply_text(
        self,
        session_id: str,
        transcript: str,
    ) -> dict[str, object]:
        interpretation = self.interpret_department_reply(transcript)
        if interpretation["status"] == "unknown":
            snapshot = {
                "service": "matia_department_call_service",
                "state": "active",
                "department_reply_transcript": transcript,
                "department_reply_interpretation": interpretation,
                "authorization_result": None,
            }
            self._runtime.save_active(session_id, snapshot)
            return snapshot

        authorization_result = self._pipeline.submit_department_response(
            session_id=session_id,
            status=interpretation["status"],
            caller_id="department-call",
            producer="matia",
        )
        finished = self.finish_call(session_id)
        snapshot = {
            "service": "matia_department_call_service",
            "state": "completed",
            "department_reply_transcript": transcript,
            "department_reply_interpretation": interpretation,
            "authorization_result": authorization_result,
            "finish_snapshot": finished,
        }
        self._runtime.save_completed(session_id, snapshot)
        self._runtime.active_path(session_id).unlink(missing_ok=True)
        return snapshot

    def submit_no_response(
        self,
        session_id: str,
        *,
        reason: str = "department_timeout",
    ) -> dict[str, object]:
        authorization_result = self._pipeline.submit_department_response(
            session_id=session_id,
            status="no_response",
            caller_id="department-call",
            producer="matia",
        )
        finished = self.finish_call(session_id)
        snapshot = {
            "service": "matia_department_call_service",
            "state": "completed",
            "department_reply_transcript": "",
            "department_reply_interpretation": {"status": "no_response", "reason": reason},
            "authorization_result": authorization_result,
            "finish_snapshot": finished,
        }
        self._runtime.save_completed(session_id, snapshot)
        self._runtime.active_path(session_id).unlink(missing_ok=True)
        return snapshot

    def submit_department_reply_audio(
        self,
        session_id: str,
        audio_file: str | Path,
    ) -> dict[str, object]:
        transcription = self._transcription_service.transcribe_file(audio_file)
        result = self.submit_department_reply_text(session_id, transcription.text)

        completed = dict(result)
        completed["department_reply_audio"] = {
            "audio_file": str(audio_file),
            "transcript": transcription.text,
            "transcription_backend": transcription.backend,
            "source_path": transcription.source_path,
        }
        self._runtime.save_completed(session_id, completed)
        return completed

    def process_reply_audio_once(self) -> dict[str, object]:
        processed: list[dict[str, object]] = []
        skipped: list[dict[str, object]] = []

        for audio_path in self._runtime.list_pending_reply_audio_files():
            session_id = audio_path.stem
            status = self.get_status(session_id)
            if not status or status.get("state") != "active":
                skipped.append(
                    {
                        "session_id": session_id,
                        "audio_file": str(audio_path),
                        "reason": "session_not_active",
                    }
                )
                continue

            result = self.submit_department_reply_audio(session_id, audio_path)
            archived_files = self._archive_reply_audio_files(audio_path)
            result_path = self._runtime.reply_audio_result_path(session_id)
            result_path.write_text(json.dumps(result, ensure_ascii=True, indent=2), encoding="utf-8")
            processed.append(
                {
                    "session_id": session_id,
                    "audio_file": str(audio_path),
                    "archived_files": archived_files,
                    "result_path": str(result_path),
                    "decision_action": result.get("authorization_result", {})
                    .get("processed_result", {})
                    .get("decision_action"),
                }
            )

        return {
            "service": "matia_department_call_service",
            "mode": "reply-audio-watch-once",
            "processed_count": len(processed),
            "processed": processed,
            "skipped_count": len(skipped),
            "skipped": skipped,
            "reply_audio_inbox": str(self._runtime.reply_audio_inbox_root),
            "reply_audio_processed": str(self._runtime.reply_audio_processed_root),
        }

    def _archive_reply_audio_files(self, audio_path: Path) -> list[str]:
        archived: list[str] = []
        for suffix in (audio_path.suffix, ".txt", ".json"):
            source = audio_path.with_suffix(suffix)
            if not source.exists():
                continue
            target = self._runtime.reply_audio_processed_root / source.name
            if target.exists():
                target.unlink()
            shutil.move(str(source), str(target))
            archived.append(str(target))
        return archived
