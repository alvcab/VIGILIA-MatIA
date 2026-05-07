import unittest

from services.decision.intent import extract_intent
from services.decision.policy import decide_from_text
from services.decision.resident_directory import ResidentDirectory
from services.tts.canned_audio import build_spoken_response


class DecisionPolicyTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_empty_text_requests_retry(self) -> None:
        decision = decide_from_text("")
        self.assertEqual(decision.action, "ask_retry")
        self.assertFalse(decision.should_open)
        self.assertEqual(decision.visitor_intent, "retry")

    def test_open_request_opens(self) -> None:
        decision = decide_from_text("abre por favor")
        self.assertEqual(decision.action, "clarify_authorization")
        self.assertFalse(decision.should_open)
        self.assertEqual(decision.visitor_intent, "access_request")

    def test_open_request_with_authorization_language_can_open(self) -> None:
        decision = decide_from_text("abre por favor, me estan esperando")
        self.assertEqual(decision.action, "open")
        self.assertTrue(decision.should_open)

    def test_open_request_with_resident_requires_confirmation_when_policy_demands_it(self) -> None:
        decision = decide_from_text("abre por favor donde Alvaro", self.directory)
        self.assertEqual(decision.action, "request_resident_confirmation")
        self.assertFalse(decision.should_open)
        self.assertEqual(decision.next_step, "ask_resident_confirmation")

    def test_greeting_requires_clarification(self) -> None:
        decision = decide_from_text("hola")
        self.assertEqual(decision.action, "greet_and_clarify")
        self.assertFalse(decision.should_open)
        self.assertEqual(decision.visitor_intent, "greeting")

    def test_resident_hint_is_detected_for_visit(self) -> None:
        decision = decide_from_text("hola, vengo donde Alvaro", self.directory)
        self.assertEqual(decision.action, "announce_resident")
        self.assertEqual(decision.resident_hint, "Alvaro")
        self.assertEqual(build_spoken_response(decision), "Entendido. Avisare a Alvaro.")

    def test_delivery_without_resident_requests_clarification(self) -> None:
        decision = decide_from_text("traigo un paquete")
        self.assertEqual(decision.action, "clarify_delivery_recipient")
        self.assertEqual(decision.visitor_intent, "delivery")
        self.assertEqual(build_spoken_response(decision), "Indica para que residente o unidad es la entrega.")

    def test_delivery_with_resident_is_announced(self) -> None:
        decision = decide_from_text("traigo un paquete para Alvaro", self.directory)
        self.assertEqual(decision.action, "announce_delivery")
        self.assertEqual(decision.resident_hint, "Alvaro")

    def test_delivery_for_resident_without_delivery_acceptance_requests_clarification(self) -> None:
        decision = decide_from_text("traigo un paquete para Conserjeria", self.directory)
        self.assertEqual(decision.action, "clarify_delivery_recipient")
        self.assertEqual(decision.reason, "resident_does_not_accept_delivery")

    def test_urgent_intent_is_escalated(self) -> None:
        decision = decide_from_text("ayuda por favor es una emergencia")
        self.assertEqual(decision.action, "escalate_urgent")
        self.assertEqual(decision.visitor_intent, "urgent")
        self.assertEqual(decision.next_step, "urgent_escalation")

    def test_reset_intent_is_detected(self) -> None:
        decision = decide_from_text("me confundi, no era aqui")
        self.assertEqual(decision.action, "reset_interaction")
        self.assertEqual(decision.visitor_intent, "reset")

    def test_intent_extraction_resolves_resident_directory(self) -> None:
        intent = extract_intent("vengo donde Alvaro Cornejo", self.directory)
        self.assertIsNotNone(intent.resident_match)
        assert intent.resident_match is not None
        self.assertEqual(intent.resident_match.display_name, "Alvaro")

    def test_unit_hint_is_resolved_to_resident(self) -> None:
        decision = decide_from_text("vengo a la casa 1", self.directory)
        self.assertEqual(decision.action, "announce_resident")
        self.assertEqual(decision.resident_hint, "Alvaro")

    def test_partial_resident_match_is_resolved(self) -> None:
        decision = decide_from_text("busco a alvaro c", self.directory)
        self.assertEqual(decision.action, "announce_resident")
        self.assertEqual(decision.resident_hint, "Alvaro")

    def test_short_resident_reply_is_resolved_without_full_phrase(self) -> None:
        decision = decide_from_text("alvaro", self.directory)
        self.assertEqual(decision.action, "announce_resident")
        self.assertEqual(decision.resident_hint, "Alvaro")

    def test_short_unit_reply_is_resolved_without_full_phrase(self) -> None:
        decision = decide_from_text("casa 1", self.directory)
        self.assertEqual(decision.action, "announce_resident")
        self.assertEqual(decision.resident_hint, "Alvaro")

    def test_greeting_generates_follow_up_prompt(self) -> None:
        decision = decide_from_text("hola")
        self.assertTrue(decision.follow_up_prompt)
        self.assertEqual(decision.next_step, "clarify_resident")
        self.assertEqual(decision.follow_up_prompt, "Solicita de forma breve a que residente o unidad viene.")

    def test_authorization_claim_without_resident_requests_specific_clarification(self) -> None:
        decision = decide_from_text("me estan esperando")
        self.assertEqual(decision.action, "clarify_resident")
        self.assertEqual(decision.reason, "authorization_claim_without_resident")
        self.assertEqual(decision.next_step, "clarify_resident_for_authorization")
        self.assertEqual(
            build_spoken_response(decision),
            "Entendido. Indica que residente o unidad autorizo tu ingreso.",
        )


if __name__ == "__main__":
    unittest.main()
