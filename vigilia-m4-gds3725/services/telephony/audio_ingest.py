from __future__ import annotations

from pathlib import Path

from services.telephony.audio_capture import AudioCapture


class LocalAudioFileIngest:
    def ingest(self, audio_file: str) -> AudioCapture:
        path = Path(audio_file)
        if not audio_file:
            raise ValueError("audio_file is required for audio-file mode")
        if not path.exists():
            raise FileNotFoundError(f"audio file not found: {path}")
        return AudioCapture(
            source_path=str(path),
            format=path.suffix.lstrip(".") or "unknown",
            transport="local-file",
        )
