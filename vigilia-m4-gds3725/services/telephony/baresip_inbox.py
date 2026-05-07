from __future__ import annotations

import json
from pathlib import Path


class BaresipInbox:
    def __init__(self, workdir: str | Path) -> None:
        workdir_path = Path(workdir)
        self._root = workdir_path / "inbox"
        self._processed = workdir_path / "processed"
        self._root.mkdir(parents=True, exist_ok=True)
        self._processed.mkdir(parents=True, exist_ok=True)

    @property
    def root(self) -> Path:
        return self._root

    @property
    def processed_root(self) -> Path:
        return self._processed

    def metadata_path_for_audio(self, audio_path: str | Path) -> Path:
        return Path(audio_path).with_suffix(".json")

    def load_metadata(self, audio_path: str | Path) -> dict[str, object]:
        metadata_path = self.metadata_path_for_audio(audio_path)
        if not metadata_path.exists():
            return {}
        payload = json.loads(metadata_path.read_text(encoding="utf-8"))
        return self.normalize_metadata(payload)

    def save_metadata(self, audio_path: str | Path, payload: dict[str, object]) -> Path:
        metadata_path = self.metadata_path_for_audio(audio_path)
        metadata_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return metadata_path

    def normalize_metadata(self, payload: dict[str, object]) -> dict[str, object]:
        normalized = dict(payload)
        face_match = normalized.get("face_match")
        if isinstance(face_match, dict):
            if "resident_id" in face_match and "face_match_resident_id" not in normalized:
                normalized["face_match_resident_id"] = face_match.get("resident_id", "")
            if "display_name" in face_match and "face_match_display_name" not in normalized:
                normalized["face_match_display_name"] = face_match.get("display_name", "")
            if "confidence" in face_match and "face_match_confidence" not in normalized:
                normalized["face_match_confidence"] = face_match.get("confidence", "")
            if "trusted" in face_match and "face_match_trusted" not in normalized:
                normalized["face_match_trusted"] = bool(face_match.get("trusted", False))
            if "checked" in face_match and "face_check_performed" not in normalized:
                normalized["face_check_performed"] = bool(face_match.get("checked", False))
        registered_visit = normalized.get("registered_visit")
        if isinstance(registered_visit, dict):
            if "code" in registered_visit and "registered_visit_code" not in normalized:
                normalized["registered_visit_code"] = str(registered_visit.get("code", ""))
        department_authorization = normalized.get("department_authorization")
        if isinstance(department_authorization, dict):
            if "status" in department_authorization and "department_authorization_status" not in normalized:
                normalized["department_authorization_status"] = str(
                    department_authorization.get("status", "")
                )
        return normalized

    def processed_result_path_for_audio(self, audio_path: str | Path) -> Path:
        return self._processed / (Path(audio_path).stem + ".result.json")

    def is_processed(self, audio_path: str | Path) -> bool:
        return self.processed_result_path_for_audio(audio_path).exists()

    def save_processed_result(self, audio_path: str | Path, payload: dict[str, object]) -> Path:
        target = self.processed_result_path_for_audio(audio_path)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target
