import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from services.telephony.audio_file_flow import AudioFileFlow
from services.transcription.service import TranscriptionService


class AudioFileFlowTests(unittest.TestCase):
    def test_audio_file_flow_uses_sidecar_transcript(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sample.wav"
            txt_path = wav_path.with_suffix(".txt")
            wav_path.write_bytes(b"RIFFfakeWAVE")
            txt_path.write_text("abre por favor", encoding="utf-8")

            result = AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file=str(wav_path),
            )

        self.assertEqual(result["mode"], "audio-file")
        self.assertEqual(result["transcription"]["backend"], "sidecar_text_stub")
        self.assertEqual(result["decision"]["action"], "clarify_authorization")
        self.assertFalse(result["gate_action"]["would_open"])
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertTrue(result["spoken_response"])

    def test_audio_file_flow_can_reach_open_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sample.wav"
            txt_path = wav_path.with_suffix(".txt")
            wav_path.write_bytes(b"RIFFfakeWAVE")
            txt_path.write_text("abre por favor, me estan esperando", encoding="utf-8")

            result = AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file=str(wav_path),
            )

        self.assertEqual(result["decision"]["action"], "open")
        self.assertTrue(result["gate_action"]["would_open"])
        self.assertFalse(result["model_guidance"]["enabled"])

    def test_audio_file_requires_existing_wav(self) -> None:
        with self.assertRaises(FileNotFoundError):
            AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file="/tmp/does-not-exist.wav",
            )

    def test_transcription_service_whisper_falls_back_to_sidecar(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sample.wav"
            txt_path = wav_path.with_suffix(".txt")
            wav_path.write_bytes(b"RIFFfakeWAVE")
            txt_path.write_text("hola fallback", encoding="utf-8")

            with patch("importlib.import_module", side_effect=ImportError("no whisper")):
                result = TranscriptionService(
                    backend_name="whisper-local",
                    whisper_model="tiny",
                ).transcribe_file(wav_path)

        self.assertEqual(result.backend, "whisper_fallback_sidecar")
        self.assertEqual(result.text, "hola fallback")


if __name__ == "__main__":
    unittest.main()
