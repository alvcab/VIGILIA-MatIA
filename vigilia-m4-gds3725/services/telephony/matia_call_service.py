from __future__ import annotations

import json
import re
import shutil
import unicodedata
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from services.transcription.service import TranscriptionService
from services.telephony.baresip_pipeline import BaresipPipeline


def _normalize_reply_text(text: str) -> str:
    lowered = " ".join(text.strip().lower().split())
    normalized = unicodedata.normalize("NFKD", lowered)
    ascii_text = "".join(char for char in normalized if not unicodedata.combining(char))
    return re.sub(r"[^a-z0-9]+", " ", ascii_text).strip()


def _contains_token_phrase(tokens: list[str], phrase: str) -> bool:
    phrase_tokens = phrase.split()
    if not phrase_tokens or len(phrase_tokens) > len(tokens):
        return False
    for index in range(len(tokens) - len(phrase_tokens) + 1):
        if tokens[index : index + len(phrase_tokens)] == phrase_tokens:
            return True
    return False


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

    def reply_audio_metadata_inbox_path(self, session_id: str) -> Path:
        return self.reply_audio_inbox_root / f"{session_id}.json"

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
            "reply_audio_capture": result.get("reply_audio_capture", {}),
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
        normalized = _normalize_reply_text(transcript)
        if not normalized:
            return {"status": "no_response", "reason": "empty_reply"}

        tokens = normalized.split()

        approved_markers = (
            "si",
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

        if any(_contains_token_phrase(tokens, marker) for marker in denied_markers):
            return {"status": "denied", "reason": "matched_denial_marker"}
        if any(_contains_token_phrase(tokens, marker) for marker in approved_markers):
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
            "transcription_error": transcription.error,
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

    def deposit_reply_audio_capture(
        self,
        session_id: str,
        source_audio_file: str | Path,
        *,
        source_label: str = "baresip-live-call",
        transport: str = "sip-udp",
    ) -> dict[str, object]:
        source = Path(source_audio_file)
        if not source.exists():
            raise FileNotFoundError(f"reply audio file not found: {source}")

        status = self.get_status(session_id) or {}
        reply_audio_capture = dict(status.get("reply_audio_capture", {}))
        target_audio = Path(
            str(reply_audio_capture.get("audio_file", self._runtime.reply_audio_inbox_path(session_id)))
        )
        target_metadata = Path(
            str(reply_audio_capture.get("metadata_file", self._runtime.reply_audio_metadata_inbox_path(session_id)))
        )

        target_audio.parent.mkdir(parents=True, exist_ok=True)
        target_metadata.parent.mkdir(parents=True, exist_ok=True)

        metadata = {
            "session_id": session_id,
            "source_label": source_label,
            "transport": transport,
            "captured_at": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "department_target": status.get("start_result", {}).get("department_target", ""),
            "target_uri": status.get("start_result", {}).get("target_uri", ""),
            "active_state": status.get("state", ""),
        }

        temp_audio = target_audio.with_suffix(target_audio.suffix + ".tmp")
        temp_metadata = target_metadata.with_suffix(target_metadata.suffix + ".tmp")
        shutil.copyfile(source, temp_audio)
        temp_metadata.write_text(json.dumps(metadata, ensure_ascii=True, indent=2), encoding="utf-8")

        sidecar_txt = source.with_suffix(".txt")
        target_txt = target_audio.with_suffix(".txt")
        temp_txt = target_txt.with_suffix(target_txt.suffix + ".tmp")
        if sidecar_txt.exists():
            shutil.copyfile(sidecar_txt, temp_txt)

        temp_metadata.replace(target_metadata)
        if sidecar_txt.exists():
            temp_txt.replace(target_txt)
        temp_audio.replace(target_audio)

        return {
            "service": "matia_department_call_service",
            "mode": "deposit-reply-audio-capture",
            "session_id": session_id,
            "audio_file": str(target_audio),
            "metadata_file": str(target_metadata),
            "sidecar_text_file": str(target_txt) if sidecar_txt.exists() else "",
            "reply_audio_capture": reply_audio_capture,
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
