from __future__ import annotations

import json
from pathlib import Path


class DepartmentAuthorizationRuntime:
    def __init__(self, workdir: str | Path) -> None:
        self._root = Path(workdir) / "department_authorization"
        self._requests = self._root / "requests"
        self._responses = self._root / "responses"
        self._processed = self._root / "processed"
        self._requests.mkdir(parents=True, exist_ok=True)
        self._responses.mkdir(parents=True, exist_ok=True)
        self._processed.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def requests_root(self) -> Path:
        return self._requests

    @property
    def responses_root(self) -> Path:
        return self._responses

    @property
    def processed_root(self) -> Path:
        return self._processed

    def request_path(self, session_id: str) -> Path:
        return self._requests / f"{session_id}.request.json"

    def response_path(self, session_id: str) -> Path:
        return self._responses / f"{session_id}.response.json"

    def processed_path(self, session_id: str) -> Path:
        return self._processed / f"{session_id}.result.json"

    def save_request(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.request_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def load_request(self, session_id: str) -> dict[str, object] | None:
        target = self.request_path(session_id)
        if not target.exists():
            return None
        return json.loads(target.read_text(encoding="utf-8"))

    def list_pending_requests(self) -> list[dict[str, object]]:
        pending: list[dict[str, object]] = []
        for request_path in sorted(self._requests.glob("*.request.json"), key=lambda path: path.stat().st_mtime):
            session_id = request_path.stem.replace(".request", "")
            if self.response_path(session_id).exists():
                continue
            if self.processed_path(session_id).exists():
                continue
            payload = json.loads(request_path.read_text(encoding="utf-8"))
            pending.append(payload)
        return pending

    def save_response(self, session_id: str, payload: dict[str, object]) -> Path:
        target = self.response_path(session_id)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target

    def load_pending_responses(self) -> list[tuple[Path, dict[str, object]]]:
        items: list[tuple[Path, dict[str, object]]] = []
        for response_path in sorted(self._responses.glob("*.response.json"), key=lambda path: path.stat().st_mtime):
            payload = json.loads(response_path.read_text(encoding="utf-8"))
            items.append((response_path, payload))
        return items

    def mark_response_processed(
        self,
        response_path: str | Path,
        payload: dict[str, object],
        result: dict[str, object],
    ) -> Path:
        response_file = Path(response_path)
        session_id = str(payload.get("session_id", response_file.stem.replace(".response", "")))
        target = self.processed_path(session_id)
        target.write_text(
            json.dumps(
                {
                    "response_event": payload,
                    "result": result,
                },
                ensure_ascii=True,
                indent=2,
            ),
            encoding="utf-8",
        )
        response_file.unlink(missing_ok=True)
        return target
