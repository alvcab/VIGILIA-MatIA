import unittest

from services.tts.matia_voice import build_department_voice_plan, build_visitor_voice_plan


class MatiaVoiceTests(unittest.TestCase):
    def test_build_visitor_voice_plan_uses_visitor_profile(self) -> None:
        plan = build_visitor_voice_plan("Hola. A que residente vienes a ver?").as_dict()

        self.assertEqual(plan["audience"], "visitor")
        self.assertEqual(plan["profile"]["profile_id"], "matia-visitor-es-cl")
        self.assertTrue(plan["interruptible"])

    def test_build_department_voice_plan_uses_department_profile(self) -> None:
        plan = build_department_voice_plan("Hola. Habla MatIA de Vigilia.").as_dict()

        self.assertEqual(plan["audience"], "department")
        self.assertEqual(plan["profile"]["profile_id"], "matia-department-es-cl")
        self.assertFalse(plan["interruptible"])


if __name__ == "__main__":
    unittest.main()
