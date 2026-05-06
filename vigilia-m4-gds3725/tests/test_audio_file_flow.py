import tempfile
import unittest
from pathlib import Path

from services.telephony.audio_file_flow import AudioFileFlow


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
        self.assertEqual(result["decision"]["action"], "open")
        self.assertTrue(result["gate_action"]["would_open"])

    def test_audio_file_requires_existing_wav(self) -> None:
        with self.assertRaises(FileNotFoundError):
            AudioFileFlow().run(
                caller_id="gds-front-door",
                audio_file="/tmp/does-not-exist.wav",
            )


if __name__ == "__main__":
    unittest.main()
