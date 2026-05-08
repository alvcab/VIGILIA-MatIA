import tempfile
import unittest
from unittest.mock import patch
from pathlib import Path

from services.decision.conversation_store import ConversationStore
from services.decision.resident_directory import ResidentDirectory
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

    def test_audio_file_flow_requires_department_before_opening_for_authorization_claim(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sample.wav"
            txt_path = wav_path.with_suffix(".txt")
            wav_path.write_bytes(b"RIFFfakeWAVE")
            txt_path.write_text("abre por favor, me estan esperando", encoding="utf-8")

            result = AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file=str(wav_path),
            )

        self.assertEqual(result["decision"]["action"], "clarify_resident")
        self.assertFalse(result["gate_action"]["would_open"])
        self.assertTrue(result["model_guidance"]["enabled"])

    def test_audio_file_requires_existing_wav(self) -> None:
        with self.assertRaises(FileNotFoundError):
            AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file="/tmp/does-not-exist.wav",
            )

    def test_audio_file_flow_can_open_from_trusted_face_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sample.wav"
            wav_path.write_bytes(b"RIFFfakeWAVE")

            flow = AudioFileFlow(
                resident_directory=ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")
            )

            result = flow.run(
                caller_id="gds-front-door",
                audio_file=str(wav_path),
                session_id="face-demo-1",
                device_label="gds3725",
                transport="sip-udp",
                face_match_resident_id="alvaro",
                face_match_display_name="Alvaro",
                face_match_confidence="high",
                face_match_trusted=True,
            )

        self.assertEqual(result["decision"]["action"], "open")
        self.assertEqual(result["decision"]["reason"], "trusted_face_match")
        self.assertTrue(result["gate_action"]["would_open"])
        self.assertEqual(result["spoken_response"], "")

    def test_audio_file_flow_can_clarify_after_no_face_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_path = Path(tmpdir) / "sample.wav"
            txt_path = wav_path.with_suffix(".txt")
            wav_path.write_bytes(b"RIFFfakeWAVE")
            txt_path.write_text("hola", encoding="utf-8")

            result = AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file=str(wav_path),
                session_id="face-demo-2",
                device_label="gds3725",
                transport="sip-udp",
                face_check_performed=True,
            )

        self.assertEqual(result["decision"]["reason"], "greeting_after_no_face_match")
        self.assertEqual(
            result["spoken_response"],
            "Hola. No reconozco tu rostro. A que residente vienes a ver?",
        )

    def test_audio_file_flow_can_complete_department_authorization_across_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            wav_first = Path(tmpdir) / "first.wav"
            wav_second = Path(tmpdir) / "second.wav"
            wav_first.write_bytes(b"RIFFfakeWAVE")
            wav_second.write_bytes(b"RIFFfakeWAVE")
            wav_first.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            wav_second.with_suffix(".txt").write_text("", encoding="utf-8")
            flow = AudioFileFlow(
                resident_directory=ResidentDirectory.from_yaml_like_file("config/residents.example.yaml"),
                conversation_store=ConversationStore(tmpdir),
            )

            first = flow.run(
                caller_id="gds-front-door",
                audio_file=str(wav_first),
                session_id="dept-audio-1",
            )
            second = flow.run(
                caller_id="gds-front-door",
                audio_file=str(wav_second),
                session_id="dept-audio-1",
                department_authorization_status="approved",
            )

        self.assertEqual(first["decision"]["action"], "contact_department")
        self.assertEqual(second["decision"]["action"], "open")
        self.assertTrue(second["gate_action"]["would_open"])

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
