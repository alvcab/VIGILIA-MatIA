import tempfile
import unittest
from pathlib import Path

from services.decision.resident_directory import ResidentDirectory
from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_pipeline import BaresipPipeline
from services.telephony.matia_call_service import MatiaCallServiceRuntime, MatiaDepartmentCallService
from services.transcription.service import TranscriptionService


class MatiaCallServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_start_and_finish_call_persist_status_snapshots(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(pipeline, runtime)

            started = service.start_call(
                request_payload={
                    "session_id": "matia-call-1",
                    "caller_id": "front-door",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                },
                call_plan={
                    "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                    "opening_text": "Hola. Habla MatIA de Vigilia.",
                    "authorization_question": "Autorizas el ingreso?",
                    "no_response_strategy": "Informar no respuesta.",
                },
                dry_run=True,
            )
            active_status = service.get_status("matia-call-1")
            finished = service.finish_call("matia-call-1")
            completed_status = service.get_status("matia-call-1")

        self.assertEqual(started["state"], "active")
        self.assertEqual(active_status["state"], "active")
        self.assertEqual(finished["state"], "completed")
        self.assertEqual(completed_status["state"], "completed")
        self.assertEqual(
            completed_status["finish_result"]["run_result"]["mode"],
            "dry-run-session",
        )

    def test_enqueue_and_run_once_promote_request_to_active(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(pipeline, runtime)

            queued = service.enqueue_call(
                request_payload={
                    "session_id": "matia-call-2",
                    "caller_id": "front-door",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                },
                call_plan={
                    "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                    "opening_text": "Hola. Habla MatIA de Vigilia.",
                    "authorization_question": "Autorizas el ingreso?",
                    "no_response_strategy": "Informar no respuesta.",
                },
                dry_run=True,
            )
            run_once = service.run_once()
            status = service.get_status("matia-call-2")

        self.assertEqual(queued["state"], "queued")
        self.assertEqual(run_once["processed_count"], 1)
        self.assertEqual(status["state"], "active")

    def test_submit_department_reply_text_approves_and_completes_session(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(pipeline, runtime)

            audio_path = workdir / "inbox" / "visit.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            pipeline.process_audio_file(
                str(audio_path),
                caller_id="front-door",
                metadata={"session_id": "matia-call-3", "caller_id": "front-door"},
            )
            service.start_call(
                request_payload={
                    "session_id": "matia-call-3",
                    "caller_id": "front-door",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                },
                call_plan={
                    "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                    "opening_text": "Hola. Habla MatIA de Vigilia.",
                    "authorization_question": "Autorizas el ingreso?",
                    "no_response_strategy": "Informar no respuesta.",
                },
                dry_run=True,
            )
            result = service.submit_department_reply_text("matia-call-3", "si, autorizado")

        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["department_reply_interpretation"]["status"], "approved")
        self.assertEqual(
            result["authorization_result"]["processed_result"]["decision_action"],
            "open",
        )

    def test_submit_no_response_requests_visit_code_when_registered_visit_exists(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(pipeline, runtime)

            audio_path = workdir / "inbox" / "visit-code.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            pipeline.process_audio_file(
                str(audio_path),
                caller_id="front-door",
                metadata={
                    "session_id": "matia-call-4",
                    "caller_id": "front-door",
                    "registered_visit": {"code": "1234"},
                },
            )
            service.start_call(
                request_payload={
                    "session_id": "matia-call-4",
                    "caller_id": "front-door",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                },
                call_plan={
                    "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                    "opening_text": "Hola. Habla MatIA de Vigilia.",
                    "authorization_question": "Autorizas el ingreso?",
                    "no_response_strategy": "Informar no respuesta.",
                },
                dry_run=True,
            )
            result = service.submit_no_response("matia-call-4")

        self.assertEqual(result["state"], "completed")
        self.assertEqual(result["department_reply_interpretation"]["status"], "no_response")
        self.assertEqual(
            result["authorization_result"]["processed_result"]["decision_action"],
            "request_visit_code",
        )

    def test_submit_department_reply_audio_uses_transcription_result(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(
                pipeline,
                runtime,
                transcription_service=TranscriptionService(backend_name="sidecar"),
            )

            audio_path = workdir / "inbox" / "department-reply.wav"
            audio_path.parent.mkdir(parents=True, exist_ok=True)
            audio_path.write_bytes(b"RIFFfakeWAVE")
            audio_path.with_suffix(".txt").write_text("no autorizado", encoding="utf-8")

            visit_audio = workdir / "inbox" / "visit-audio.wav"
            visit_audio.write_bytes(b"RIFFfakeWAVE")
            visit_audio.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            pipeline.process_audio_file(
                str(visit_audio),
                caller_id="front-door",
                metadata={"session_id": "matia-call-5", "caller_id": "front-door"},
            )
            service.start_call(
                request_payload={
                    "session_id": "matia-call-5",
                    "caller_id": "front-door",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                },
                call_plan={
                    "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                    "opening_text": "Hola. Habla MatIA de Vigilia.",
                    "authorization_question": "Autorizas el ingreso?",
                    "no_response_strategy": "Informar no respuesta.",
                },
                dry_run=True,
            )
            result = service.submit_department_reply_audio("matia-call-5", audio_path)

        self.assertEqual(result["department_reply_audio"]["transcript"], "no autorizado")
        self.assertEqual(result["department_reply_interpretation"]["status"], "denied")
        self.assertEqual(
            result["authorization_result"]["processed_result"]["decision_action"],
            "deny_access",
        )

    def test_process_reply_audio_once_consumes_inbox_and_archives_files(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(
                pipeline,
                runtime,
                transcription_service=TranscriptionService(backend_name="sidecar"),
            )

            visit_audio = workdir / "inbox" / "visit-watch.wav"
            visit_audio.parent.mkdir(parents=True, exist_ok=True)
            visit_audio.write_bytes(b"RIFFfakeWAVE")
            visit_audio.with_suffix(".txt").write_text("vengo donde Alvaro", encoding="utf-8")
            pipeline.process_audio_file(
                str(visit_audio),
                caller_id="front-door",
                metadata={"session_id": "matia-call-6", "caller_id": "front-door"},
            )
            service.start_call(
                request_payload={
                    "session_id": "matia-call-6",
                    "caller_id": "front-door",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                },
                call_plan={
                    "voice_plan": {"profile": {"profile_id": "matia-department-es-cl"}},
                    "opening_text": "Hola. Habla MatIA de Vigilia.",
                    "authorization_question": "Autorizas el ingreso?",
                    "no_response_strategy": "Informar no respuesta.",
                },
                dry_run=True,
            )

            reply_audio = runtime.reply_audio_inbox_path("matia-call-6")
            reply_audio.write_bytes(b"RIFFfakeWAVE")
            reply_audio.with_suffix(".txt").write_text("si, autorizado", encoding="utf-8")

            result = service.process_reply_audio_once()
            reply_audio_exists = reply_audio.exists()
            reply_audio_txt_exists = reply_audio.with_suffix(".txt").exists()
            archived_wav_exists = (runtime.reply_audio_processed_root / "matia-call-6.wav").exists()
            archived_txt_exists = (runtime.reply_audio_processed_root / "matia-call-6.txt").exists()
            result_json_exists = runtime.reply_audio_result_path("matia-call-6").exists()

        self.assertEqual(result["processed_count"], 1)
        self.assertEqual(result["skipped_count"], 0)
        self.assertEqual(result["processed"][0]["decision_action"], "open")
        self.assertFalse(reply_audio_exists)
        self.assertFalse(reply_audio_txt_exists)
        self.assertTrue(archived_wav_exists)
        self.assertTrue(archived_txt_exists)
        self.assertTrue(result_json_exists)

    def test_process_reply_audio_once_skips_unknown_or_inactive_session(self) -> None:
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
            runtime = MatiaCallServiceRuntime.from_workdir(workdir)
            service = MatiaDepartmentCallService(
                pipeline,
                runtime,
                transcription_service=TranscriptionService(backend_name="sidecar"),
            )

            reply_audio = runtime.reply_audio_inbox_path("unknown-session")
            reply_audio.write_bytes(b"RIFFfakeWAVE")
            reply_audio.with_suffix(".txt").write_text("si, autorizado", encoding="utf-8")

            result = service.process_reply_audio_once()
            reply_audio_exists = reply_audio.exists()

        self.assertEqual(result["processed_count"], 0)
        self.assertEqual(result["skipped_count"], 1)
        self.assertEqual(result["skipped"][0]["reason"], "session_not_active")
        self.assertTrue(reply_audio_exists)


if __name__ == "__main__":
    unittest.main()
