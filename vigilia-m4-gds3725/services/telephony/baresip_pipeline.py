from __future__ import annotations

from pathlib import Path

from pathlib import Path

from services.decision.resident_directory import ResidentDirectory
from services.telephony.audio_file_flow import AudioFileFlow
from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_inbox import BaresipInbox


class BaresipPipeline:
    def __init__(
        self,
        resident_directory: ResidentDirectory | None = None,
        *,
        transcription_backend_name: str = "sidecar",
        whisper_model: str = "tiny",
        model_backend_name: str = "stub",
        ollama_model: str = "vigilia-mini",
        ollama_timeout_seconds: float = 8.0,
        baresip_config: BaresipConfig | None = None,
    ) -> None:
        self._baresip_config = baresip_config or BaresipConfig.from_env()
        self._inbox = BaresipInbox(self._baresip_config.workdir)
        self._audio_flow = AudioFileFlow(
            resident_directory=resident_directory,
            transcription_backend_name=transcription_backend_name,
            whisper_model=whisper_model,
            model_backend_name=model_backend_name,
            ollama_model=ollama_model,
            ollama_timeout_seconds=ollama_timeout_seconds,
        )

    def process_audio_file(self, audio_file: str, caller_id: str) -> dict[str, object]:
        result = self._audio_flow.run(caller_id=caller_id, audio_file=audio_file)
        result["mode"] = "baresip-inbox"
        result["baresip_inbox"] = {
            "workdir": self._baresip_config.workdir,
            "inbox_dir": str(self._inbox.root),
            "processed_dir": str(self._inbox.processed_root),
            "metadata": self._inbox.load_metadata(audio_file),
        }
        return result

    def process_latest(self) -> dict[str, object]:
        candidates = sorted(self._inbox.root.glob("*.wav"), key=lambda path: path.stat().st_mtime, reverse=True)
        if not candidates:
            raise FileNotFoundError("no baresip inbox wav files found")

        latest = candidates[0]
        metadata = self._inbox.load_metadata(latest)
        caller_id = str(metadata.get("caller_id", "baresip-inbox"))
        return self.process_audio_file(str(latest), caller_id=caller_id)

    def process_new_files_once(self) -> dict[str, object]:
        processed: list[dict[str, object]] = []
        skipped: list[str] = []

        candidates = sorted(self._inbox.root.glob("*.wav"), key=lambda path: path.stat().st_mtime)
        for candidate in candidates:
            if self._inbox.is_processed(candidate):
                skipped.append(str(candidate))
                continue

            metadata = self._inbox.load_metadata(candidate)
            caller_id = str(metadata.get("caller_id", "baresip-inbox"))
            result = self.process_audio_file(str(candidate), caller_id=caller_id)
            result_path = self._inbox.save_processed_result(candidate, result)
            processed.append(
                {
                    "audio_file": str(candidate),
                    "caller_id": caller_id,
                    "result_path": str(result_path),
                    "decision_action": result["decision"]["action"],
                }
            )

        return {
            "mode": "baresip-watch-once",
            "processed_count": len(processed),
            "processed": processed,
            "skipped_count": len(skipped),
            "skipped": skipped,
            "inbox_dir": str(self._inbox.root),
            "processed_dir": str(self._inbox.processed_root),
        }
