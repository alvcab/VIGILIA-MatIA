import unittest

from services.decision.resident_directory import ResidentDirectory
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


if __name__ == "__main__":
    unittest.main()
