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
        return json.loads(metadata_path.read_text(encoding="utf-8"))

    def save_metadata(self, audio_path: str | Path, payload: dict[str, object]) -> Path:
        metadata_path = self.metadata_path_for_audio(audio_path)
        metadata_path.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return metadata_path

    def processed_result_path_for_audio(self, audio_path: str | Path) -> Path:
        return self._processed / (Path(audio_path).stem + ".result.json")

    def is_processed(self, audio_path: str | Path) -> bool:
        return self.processed_result_path_for_audio(audio_path).exists()

    def save_processed_result(self, audio_path: str | Path, payload: dict[str, object]) -> Path:
        target = self.processed_result_path_for_audio(audio_path)
        target.write_text(json.dumps(payload, ensure_ascii=True, indent=2), encoding="utf-8")
        return target
