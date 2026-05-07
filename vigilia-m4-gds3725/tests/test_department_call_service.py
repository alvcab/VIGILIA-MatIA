import unittest

from services.decision.resident_directory import ResidentDirectory
from services.telephony.baresip_config import BaresipConfig
from services.telephony.department_call_service import DepartmentCallService
from services.telephony.sip_config import SipEndpointConfig


class DepartmentCallServiceTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_build_execution_plan_uses_department_sip_uri(self) -> None:
        service = DepartmentCallService(
            resident_directory=self.directory,
            sip_config=SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.100.50",
                local_port=5062,
                transport="udp",
            ),
            baresip_config=BaresipConfig(
                binary="baresip",
                config_path="runtime/baresip/config",
                accounts_path="runtime/baresip/accounts",
                audio_path="runtime/baresip/audio",
                workdir="runtime/baresip",
            ),
        )
        plan = service.build_execution_plan(
            request_payload={
                "session_id": "dept-call-1",
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
        ).as_dict()

        self.assertEqual(plan["target_uri"], "sip:depto1@192.168.100.71:5060;transport=udp")
        self.assertEqual(plan["local_uri"], "sip:vigilia@192.168.100.50:5062;transport=udp")
        self.assertEqual(plan["invite_preview"]["to_uri"], plan["target_uri"])
        self.assertEqual(plan["baresip_execution_preview"]["target_uri"], plan["target_uri"])
        self.assertEqual(
            plan["baresip_execution_preview"]["startup_command"],
            ["baresip", "-f", "runtime/baresip/config"],
        )
        self.assertEqual(
            plan["baresip_execution_preview"]["dial_command"],
            f"/dial {plan['target_uri']}",
        )

    def test_run_execution_plan_returns_dry_run_result(self) -> None:
        service = DepartmentCallService(
            resident_directory=self.directory,
            sip_config=SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.100.50",
                local_port=5062,
                transport="udp",
            ),
            baresip_config=BaresipConfig(
                binary="baresip",
                config_path="runtime/baresip/config",
                accounts_path="runtime/baresip/accounts",
                audio_path="runtime/baresip/audio",
                workdir="runtime/baresip",
            ),
        )
        execution_plan = service.build_execution_plan(
            request_payload={
                "session_id": "dept-call-2",
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
        )

        result = service.run_execution_plan(execution_plan, dry_run=True)

        self.assertEqual(result["session_id"], "dept-call-2")
        self.assertEqual(result["run_result"]["mode"], "dry-run")
        self.assertFalse(result["run_result"]["started"])

    def test_start_and_finish_execution_session_return_structured_results(self) -> None:
        service = DepartmentCallService(
            resident_directory=self.directory,
            sip_config=SipEndpointConfig(
                device_label="gds3725",
                local_user="vigilia",
                local_domain="192.168.100.50",
                local_port=5062,
                transport="udp",
            ),
            baresip_config=BaresipConfig(
                binary="baresip",
                config_path="runtime/baresip/config",
                accounts_path="runtime/baresip/accounts",
                audio_path="runtime/baresip/audio",
                workdir="runtime/baresip",
            ),
        )
        execution_plan = service.build_execution_plan(
            request_payload={
                "session_id": "dept-call-3",
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
        )

        started = service.start_execution_session(execution_plan, dry_run=True)
        finished = service.finish_execution_session("dept-call-3")

        self.assertEqual(started["call_session"]["session_id"], "dept-call-3")
        self.assertTrue(started["call_session"]["started"])
        self.assertEqual(finished["run_result"]["mode"], "dry-run-session")


if __name__ == "__main__":
    unittest.main()
