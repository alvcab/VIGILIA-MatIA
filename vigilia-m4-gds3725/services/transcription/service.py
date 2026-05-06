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
        source = Path(path)
        source_path = str(source)
        sidecar_text_path = source.with_suffix(".txt")
        transcript_text = ""

        if sidecar_text_path.exists():
            transcript_text = sidecar_text_path.read_text(encoding="utf-8").strip()

        return TranscriptionResult(
            text=transcript_text,
            source_path=source_path,
            backend="sidecar_text_stub",
        )
