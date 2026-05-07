import tempfile
import unittest
from pathlib import Path

from services.decision.resident_directory import ResidentDirectory
from services.telephony.baresip_config import BaresipConfig
from services.telephony.baresip_pipeline import BaresipPipeline
from services.telephony.matia_call_service import MatiaCallServiceRuntime, MatiaDepartmentCallService


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


if __name__ == "__main__":
    unittest.main()
