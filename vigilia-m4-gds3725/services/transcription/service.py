from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    source_path: str
    backend: str


class TranscriptionService:
    def transcribe_file(self, path: str | Path) -> TranscriptionResult:
        source_path = str(Path(path))
        return TranscriptionResult(
            text="",
            source_path=source_path,
            backend="not_implemented_yet",
        )
