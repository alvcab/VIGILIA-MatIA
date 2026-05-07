import unittest

from services.telephony.department_call_plan import DepartmentCallRequest, build_department_call_plan


class DepartmentCallPlanTests(unittest.TestCase):
    def test_build_department_call_plan_for_visit(self) -> None:
        plan = build_department_call_plan(
            DepartmentCallRequest(
                session_id="session-1",
                caller_id="front-door",
                resident_candidate="Alvaro",
                department_target="Departamento 1",
                current_intent="visit",
                registered_visit_available=False,
            )
        ).as_dict()

        self.assertEqual(plan["target_label"], "Departamento 1")
        self.assertIn("Habla MatIA de Vigilia", plan["opening_text"])
        self.assertIn("aprobado, rechazado o sin respuesta", plan["authorization_question"])
        self.assertEqual(
            plan["voice_plan"]["profile"]["profile_id"],
            "matia-department-es-cl",
        )

    def test_build_department_call_plan_mentions_code_fallback_when_registered_visit_exists(self) -> None:
        plan = build_department_call_plan(
            DepartmentCallRequest(
                session_id="session-2",
                caller_id="front-door",
                resident_candidate="Alvaro",
                department_target="Departamento 1",
                current_intent="visit",
                registered_visit_available=True,
            )
        ).as_dict()

        self.assertIn("codigo de 4 digitos", plan["no_response_strategy"])


if __name__ == "__main__":
    unittest.main()
