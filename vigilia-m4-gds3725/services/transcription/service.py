from __future__ import annotations

from dataclasses import dataclass
import importlib
from pathlib import Path


@dataclass(frozen=True)
class TranscriptionResult:
    text: str
    source_path: str
    backend: str


class TranscriptionService:
    def __init__(self, backend_name: str = "sidecar", whisper_model: str = "tiny") -> None:
        self._backend_name = backend_name
        self._whisper_model = whisper_model

    def _transcribe_with_sidecar(self, source: Path) -> TranscriptionResult:
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

    def _transcribe_with_whisper(self, source: Path) -> TranscriptionResult:
        source_path = str(source)
        try:
            whisper_module = importlib.import_module("whisper")
            model = whisper_module.load_model(self._whisper_model)
            result = model.transcribe(source_path)
            text = (result.get("text") or "").strip()
            return TranscriptionResult(
                text=text,
                source_path=source_path,
                backend=f"whisper_local:{self._whisper_model}",
            )
        except Exception:
            fallback = self._transcribe_with_sidecar(source)
            return TranscriptionResult(
                text=fallback.text,
                source_path=source_path,
                backend="whisper_fallback_sidecar",
            )

    def transcribe_file(self, path: str | Path) -> TranscriptionResult:
        source = Path(path)
        normalized_backend = self._backend_name.strip().lower()
        if normalized_backend == "whisper-local":
            return self._transcribe_with_whisper(source)
        return self._transcribe_with_sidecar(source)
