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

    def test_process_latest_can_use_trusted_face_match_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            audio_path = workdir / "inbox" / "face.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            inbox = BaresipInbox(workdir)
            inbox.save_metadata(
                audio_path,
                {
                    "session_id": "face-session-1",
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "face_match_resident_id": "alvaro",
                    "face_match_display_name": "Alvaro",
                    "face_match_confidence": "high",
                    "face_match_trusted": True,
                },
            )

            result = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            ).process_latest()

        self.assertEqual(result["decision"]["action"], "open")
        self.assertEqual(result["decision"]["reason"], "trusted_face_match")
        self.assertTrue(result["gate_action"]["would_open"])
        self.assertEqual(result["session"]["session_id"], "face-session-1")

    def test_process_latest_can_use_nested_face_match_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            audio_path = workdir / "inbox" / "face-nested.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            inbox = BaresipInbox(workdir)
            inbox.save_metadata(
                audio_path,
                {
                    "session_id": "face-session-2",
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "face_match": {
                        "resident_id": "alvaro",
                        "display_name": "Alvaro",
                        "confidence": "high",
                        "trusted": True,
                    },
                },
            )

            result = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            ).process_latest()

        self.assertEqual(result["decision"]["action"], "open")
        self.assertEqual(result["decision"]["reason"], "trusted_face_match")
        self.assertTrue(result["gate_action"]["would_open"])
        self.assertEqual(result["session"]["session_id"], "face-session-2")
        self.assertEqual(
            result["baresip_inbox"]["metadata"]["face_match_display_name"],
            "Alvaro",
        )

    def test_process_latest_can_clarify_after_checked_face_no_match(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            audio_path = workdir / "inbox" / "face-no-match.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("hola", encoding="utf-8")
            inbox = BaresipInbox(workdir)
            inbox.save_metadata(
                audio_path,
                {
                    "session_id": "face-session-3",
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "face_match": {
                        "checked": True,
                        "trusted": False,
                    },
                },
            )

            result = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            ).process_latest()

        self.assertEqual(result["decision"]["reason"], "greeting_after_no_face_match")
        self.assertEqual(
            result["spoken_response"],
            "Hola. No reconozco tu rostro. A que residente vienes a ver?",
        )

    def test_process_audio_file_can_use_department_authorization_and_registered_visit_metadata(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            pipeline = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            )

            first_audio = workdir / "inbox" / "visit.wav"
            second_audio = workdir / "inbox" / "visit-follow-up.wav"
            first_audio.parent.mkdir(parents=True, exist_ok=True)
            first_audio.write_bytes(b"RIFFfakeWAVE")
            second_audio.write_bytes(b"RIFFfakeWAVE")
            first_audio.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            second_audio.with_suffix(".txt").write_text("", encoding="utf-8")

            first = pipeline.process_audio_file(
                str(first_audio),
                caller_id="front-door",
                metadata={
                    "session_id": "dept-session-1",
                    "caller_id": "front-door",
                    "registered_visit": {"code": "1234"},
                },
            )
            second = pipeline.process_audio_file(
                str(second_audio),
                caller_id="front-door",
                metadata={
                    "session_id": "dept-session-1",
                    "caller_id": "front-door",
                    "department_authorization": {"status": "no_response"},
                },
            )

        self.assertEqual(first["decision"]["action"], "contact_department")
        self.assertEqual(second["decision"]["action"], "request_visit_code")
        self.assertTrue(second["conversation_state"]["memory"]["waiting_for_visit_code"])

    def test_contact_department_creates_request_artifact(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            pipeline = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            )

            audio_path = workdir / "inbox" / "contact.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")

            result = pipeline.process_audio_file(
                str(audio_path),
                caller_id="front-door",
                metadata={
                    "session_id": "dept-request-1",
                    "caller_id": "front-door",
                },
            )
            self.assertEqual(result["decision"]["action"], "contact_department")
            self.assertIn("department_authorization_request", result)
            self.assertTrue(
                Path(result["department_authorization_request"]["request_path"]).exists()
            )
            self.assertEqual(
                result["department_authorization_request"]["payload"]["department_target"],
                "Departamento 1",
            )
        self.assertEqual(
            result["department_authorization_request"]["call_plan_for_matia"]["voice_plan"]["profile"]["profile_id"],
            "matia-department-es-cl",
        )
        self.assertEqual(
            result["department_authorization_request"]["baresip_outgoing_call_preview"]["target_uri"],
            "sip:depto1@192.168.100.71:5060;transport=udp",
        )

    def test_process_department_responses_once_consumes_response_events(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            pipeline = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            )

            first_audio = workdir / "inbox" / "dept-response.wav"
            first_audio.parent.mkdir(parents=True, exist_ok=True)
            first_audio.write_bytes(b"RIFFfakeWAVE")
            first_audio.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            pipeline.process_audio_file(
                str(first_audio),
                caller_id="front-door",
                metadata={
                    "session_id": "dept-response-1",
                    "caller_id": "front-door",
                },
            )

            response_path = workdir / "department_authorization" / "responses" / "dept-response-1.response.json"
            response_path.parent.mkdir(parents=True, exist_ok=True)
            response_path.write_text(
                '{\n'
                '  "session_id": "dept-response-1",\n'
                '  "caller_id": "front-door",\n'
                '  "department_authorization": {"status": "approved"}\n'
                '}\n',
                encoding="utf-8",
            )

            result = pipeline.process_department_responses_once()
            self.assertEqual(result["mode"], "department-watch-once")
            self.assertEqual(result["processed_count"], 1)
            self.assertEqual(result["processed"][0]["decision_action"], "open")

    def test_submit_department_response_processes_event_for_matia_directly(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            workdir = Path(tmpdir) / "baresip"
            config = BaresipConfig(
                binary="baresip",
                config_path=str(workdir / "config"),
                accounts_path=str(workdir / "accounts"),
                audio_path=str(workdir / "audio"),
                workdir=str(workdir),
            )
            pipeline = BaresipPipeline(
                resident_directory=self.directory,
                baresip_config=config,
            )

            first_audio = workdir / "inbox" / "matia-direct.wav"
            first_audio.parent.mkdir(parents=True, exist_ok=True)
            first_audio.write_bytes(b"RIFFfakeWAVE")
            first_audio.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            pipeline.process_audio_file(
                str(first_audio),
                caller_id="front-door",
                metadata={
                    "session_id": "matia-direct-1",
                    "caller_id": "front-door",
                },
            )

            result = pipeline.submit_department_response(
                session_id="matia-direct-1",
                status="approved",
                caller_id="front-door",
            )

        self.assertEqual(result["mode"], "department-submit-response")
        self.assertEqual(result["response_event"]["payload"]["producer"], "matia")
        self.assertIsNotNone(result["processed_result"])
        self.assertEqual(result["processed_result"]["decision_action"], "open")
