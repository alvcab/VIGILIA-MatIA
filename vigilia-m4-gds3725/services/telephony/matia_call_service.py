from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path

from services.telephony.baresip_pipeline import BaresipPipeline


@dataclass(frozen=True)
class MatiaCallServiceRuntime:
    root: Path
    active_root: Path
    completed_root: Path

    @classmethod
    def from_workdir(cls, workdir: str | Path) -> "MatiaCallServiceRuntime":
        root = Path(workdir) / "matia_call_service"
        active_root = root / "active"
        completed_root = root / "completed"
        active_root.mkdir(parents=True, exist_ok=True)
        completed_root.mkdir(parents=True, exist_ok=True)
        return cls(root=root, active_root=active_root, completed_root=completed_root)

    def active_path(self, session_id: str) -> Path:
        return self.active_root / f"{session_id}.active.json"

    def completed_path(self, session_id: str) -> Path:
        return self.completed_root / f"{session_id}.completed.json"

    def save_active(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.active_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def save_completed(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.completed_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def load_status(self, session_id: str) -> dict[str, object] | None:
        active = self.active_path(session_id)
        if active.exists():
            return json.loads(active.read_text(encoding="utf-8"))
        completed = self.completed_path(session_id)
        if completed.exists():
            return json.loads(completed.read_text(encoding="utf-8"))
        return None


class MatiaDepartmentCallService:
    def __init__(self, pipeline: BaresipPipeline, runtime: MatiaCallServiceRuntime) -> None:
        self._pipeline = pipeline
        self._runtime = runtime

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
