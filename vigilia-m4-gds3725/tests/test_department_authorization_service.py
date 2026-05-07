import tempfile
import unittest
from pathlib import Path

from services.telephony.department_authorization_runtime import DepartmentAuthorizationRuntime
from services.telephony.department_authorization_service import DepartmentAuthorizationService


class DepartmentAuthorizationServiceTests(unittest.TestCase):
    def test_lists_only_pending_requests(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = DepartmentAuthorizationRuntime(Path(tmpdir) / "baresip")
            service = DepartmentAuthorizationService(runtime)
            runtime.save_request(
                "session-1",
                {
                    "session_id": "session-1",
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                    "current_intent": "visit",
                    "registered_visit_available": False,
                },
            )
            runtime.save_request(
                "session-2",
                {
                    "session_id": "session-2",
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                    "current_intent": "visit",
                    "registered_visit_available": False,
                },
            )
            runtime.save_response(
                "session-2",
                {
                    "session_id": "session-2",
                    "department_authorization": {"status": "approved"},
                },
            )

            pending = service.list_pending_requests()

        self.assertEqual(len(pending), 1)
        self.assertEqual(pending[0].session_id, "session-1")

    def test_create_response_uses_request_defaults(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = DepartmentAuthorizationRuntime(Path(tmpdir) / "baresip")
            service = DepartmentAuthorizationService(runtime)
            runtime.save_request(
                "session-3",
                {
                    "session_id": "session-3",
                    "caller_id": "front-door",
                    "device_label": "gds3725",
                    "transport": "sip-udp",
                    "resident_candidate": "Alvaro",
                    "department_target": "Departamento 1",
                    "current_intent": "visit",
                    "registered_visit_available": True,
                },
            )

            result = service.create_response("session-3", "no_response")
            self.assertEqual(result["mode"], "department-respond")
            self.assertTrue(result["request_found"])
            self.assertTrue(Path(result["response_path"]).exists())
            self.assertEqual(
                result["payload"]["department_authorization"]["department_target"],
                "Departamento 1",
            )

    def test_create_response_rejects_invalid_status(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            runtime = DepartmentAuthorizationRuntime(Path(tmpdir) / "baresip")
            service = DepartmentAuthorizationService(runtime)

            with self.assertRaises(ValueError):
                service.create_response("session-4", "maybe")


if __name__ == "__main__":
    unittest.main()
