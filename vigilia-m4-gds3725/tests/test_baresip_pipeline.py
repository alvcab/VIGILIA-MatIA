import tempfile
import unittest
from pathlib import Path

from services.decision.resident_directory import ResidentDirectory
from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_inbox import BaresipInbox
from services.telephony.baresip_pipeline import BaresipPipeline


class BaresipPipelineTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_process_audio_file_runs_end_to_end(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            audio_path = workdir / "inbox" / "demo.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("hola", encoding="utf-8")
            BaresipInbox(workdir).save_metadata(audio_path, {"caller_id": "front-door"})

            result = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            ).process_latest()

        self.assertEqual(result["mode"], "baresip-inbox")
        self.assertEqual(result["session"]["caller_id"], "front-door")
        self.assertEqual(result["decision"]["action"], "greet_and_clarify")
        self.assertEqual(result["baresip_inbox"]["metadata"]["caller_id"], "front-door")

    def test_process_new_files_once_writes_processed_results(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            inbox = BaresipInbox(workdir)
            audio_path = inbox.root / "demo.wav"
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("hola", encoding="utf-8")
            inbox.save_metadata(
                audio_path,
                {
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "received_at": "2026-05-06T18:30:00+00:00",
                },
            )

            result = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            ).process_new_files_once()

        self.assertEqual(result["mode"], "baresip-watch-once")
        self.assertEqual(result["processed_count"], 1)
        self.assertEqual(result["processed"][0]["decision_action"], "greet_and_clarify")
        self.assertEqual(result["processed"][0]["caller_id"], "front-door")
