import tempfile
import unittest

from services.decision.conversation_store import ConversationStore
from services.decision.resident_directory import ResidentDirectory
from services.decision.turn_evaluator import TurnEvaluator, TurnInput


class TurnEvaluatorTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_evaluate_turn_returns_structured_payload_for_matia(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-1",
                    caller_id="front-door",
                    transcript="hola",
                )
            )

        self.assertEqual(result["mode"], "turn-evaluation")
        self.assertEqual(result["session"]["session_id"], "demo-1")
        self.assertEqual(result["decision"]["action"], "greet_and_clarify")
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertEqual(result["session_memory"]["current_intent"], "greeting")
        self.assertEqual(result["conversation_state"]["turn_count"], 2)
        self.assertEqual(result["conversation_state"]["turns"][0]["speaker"], "visitor")
        self.assertEqual(result["conversation_state"]["turns"][1]["speaker"], "matia")
        self.assertEqual(result["conversation_state"]["turns"][1]["text"], result["spoken_response"])

    def test_evaluate_turn_persists_follow_up_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            first = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-2",
                    caller_id="front-door",
                    transcript="hola",
                )
            )
            second = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-2",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                )
            )

        self.assertEqual(first["conversation_state"]["turn_count"], 2)
        self.assertEqual(second["conversation_state"]["turn_count"], 4)
        self.assertEqual(second["decision"]["resident_hint"], "Alvaro")
        self.assertEqual(second["session_memory"]["resident_candidate"], "Alvaro")
        self.assertTrue(second["session_memory"]["waiting_for_department_response"])
        self.assertEqual(second["conversation_state"]["turns"][2]["text"], "vengo donde Alvaro")
        self.assertEqual(second["conversation_state"]["turns"][3]["speaker"], "matia")
        self.assertEqual(second["decision"]["action"], "contact_department")
        self.assertEqual(second["spoken_response"], "Un momento. Llamare al departamento 1.")

    def test_trusted_face_match_opens_immediately(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-face-1",
                    caller_id="front-door",
                    transcript="",
                    face_match_resident_id="alvaro",
                    face_match_display_name="Alvaro",
                    face_match_confidence="high",
                    face_match_trusted=True,
                )
            )

        self.assertEqual(result["decision"]["action"], "open")
        self.assertTrue(result["gate_action"]["would_open"])
        self.assertEqual(result["decision"]["reason"], "trusted_face_match")
        self.assertEqual(result["decision"]["resident_hint"], "Alvaro")
        self.assertFalse(result["model_guidance"]["enabled"])
        self.assertEqual(result["session_memory"]["face_recognition_result"], "trusted_match")
        self.assertEqual(result["spoken_response"], "")

    def test_unknown_trusted_face_match_does_not_open(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-face-unknown",
                    caller_id="front-door",
                    transcript="",
                    face_match_resident_id="desconocido",
                    face_match_display_name="Persona Desconocida",
                    face_match_confidence="high",
                    face_match_trusted=True,
                )
            )

        self.assertNotEqual(result["decision"]["action"], "open")
        self.assertFalse(result["gate_action"]["would_open"])
        self.assertEqual(result["session_memory"]["face_recognition_result"], "no_match")

    def test_no_face_match_prompts_for_resident_with_clearer_response(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-face-2",
                    caller_id="front-door",
                    transcript="hola",
                    face_check_performed=True,
                )
            )

        self.assertEqual(result["decision"]["action"], "greet_and_clarify")
        self.assertEqual(result["decision"]["reason"], "greeting_after_no_face_match")
        self.assertEqual(
            result["spoken_response"],
            "Hola. No reconozco tu rostro. A que residente vienes a ver?",
        )
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "No reconozco tu rostro. Dime a que residente o departamento vienes.",
        )
        self.assertEqual(result["session_memory"]["face_recognition_result"], "no_match")

    def test_authorization_claim_without_resident_gets_specific_follow_up(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-auth-1",
                    caller_id="front-door",
                    transcript="me estan esperando",
                )
            )

        self.assertEqual(result["decision"]["reason"], "authorization_claim_without_resident")
        self.assertEqual(
            result["spoken_response"],
            "Indica que residente o departamento autorizo tu ingreso.",
        )
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Indica que residente o departamento autorizo tu ingreso.",
        )

    def test_second_turn_short_resident_reply_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            first = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-short-1",
                    caller_id="front-door",
                    transcript="hola",
                )
            )
            second = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-short-1",
                    caller_id="front-door",
                    transcript="alvaro",
                )
            )

        self.assertEqual(first["decision"]["action"], "greet_and_clarify")
        self.assertEqual(second["decision"]["action"], "contact_department")
        self.assertEqual(second["decision"]["resident_hint"], "Alvaro")
        self.assertEqual(second["session_memory"]["resident_candidate"], "Alvaro")
        self.assertEqual(second["spoken_response"], "Un momento. Llamare al departamento 1.")

    def test_second_turn_short_unit_reply_is_resolved(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-short-2",
                    caller_id="front-door",
                    transcript="traigo un paquete",
                )
            )
            second = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-short-2",
                    caller_id="front-door",
                    transcript="depto 1",
                )
            )

        self.assertEqual(second["decision"]["action"], "contact_department")
        self.assertEqual(second["decision"]["resident_hint"], "Alvaro")
        self.assertEqual(second["session_memory"]["unit_candidate"], "depto 1")

    def test_department_approval_opens_gate(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-1",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                )
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-1",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="approved",
                )
            )

        self.assertEqual(result["decision"]["action"], "open")
        self.assertEqual(result["decision"]["reason"], "department_authorized_access")
        self.assertTrue(result["gate_action"]["would_open"])
        self.assertEqual(result["spoken_response"], "Abriendo.")

    def test_department_approval_without_pending_request_is_rejected(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-unexpected",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="approved",
                )
            )

        self.assertEqual(result["decision"]["action"], "deny_access")
        self.assertEqual(result["decision"]["reason"], "unexpected_department_authorization")
        self.assertFalse(result["gate_action"]["would_open"])

    def test_department_denial_rejects_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-2",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                )
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-2",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="denied",
                )
            )

        self.assertEqual(result["decision"]["action"], "deny_access")
        self.assertEqual(result["spoken_response"], "Lo siento, no esta autorizado.")
        self.assertFalse(result["gate_action"]["would_open"])

    def test_department_no_response_without_registered_visit_reports_no_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-3",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                )
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-3",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="no_response",
                )
            )

        self.assertEqual(result["decision"]["action"], "deny_access")
        self.assertEqual(result["decision"]["reason"], "department_no_response")
        self.assertEqual(result["spoken_response"], "No tengo respuesta del departamento 1.")

    def test_department_no_response_with_registered_visit_requests_code(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-4",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                    registered_visit_code="1234",
                )
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-4",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="no_response",
                )
            )

        self.assertEqual(result["decision"]["action"], "request_visit_code")
        self.assertTrue(result["session_memory"]["waiting_for_visit_code"])
        self.assertIn("codigo de autorizacion de 4 digitos", result["spoken_response"])

    def test_registered_visit_code_can_open_when_department_does_not_answer(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-5",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                    registered_visit_code="1234",
                )
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-5",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="no_response",
                )
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-5",
                    caller_id="front-door",
                    transcript="mi codigo es 1234",
                )
            )

        self.assertEqual(result["decision"]["action"], "open")
        self.assertEqual(result["decision"]["reason"], "registered_visit_code_valid")
        self.assertTrue(result["gate_action"]["would_open"])

    def test_invalid_registered_visit_code_rejects_access(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-6",
                    caller_id="front-door",
                    transcript="vengo donde Alvaro",
                    registered_visit_code="1234",
                )
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-6",
                    caller_id="front-door",
                    transcript="",
                    department_authorization_status="no_response",
                )
            )
            result = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-dept-6",
                    caller_id="front-door",
                    transcript="mi codigo es 9999",
                )
            )

        self.assertEqual(result["decision"]["action"], "deny_access")
        self.assertEqual(result["decision"]["reason"], "registered_visit_code_invalid")
        self.assertEqual(result["spoken_response"], "Lo siento, no esta autorizado.")

    def test_follow_up_prompt_includes_recent_conversation_summary(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            evaluator = TurnEvaluator(
                resident_directory=self.directory,
                conversation_store=ConversationStore(tmpdir),
            )
            evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-summary-1",
                    caller_id="front-door",
                    transcript="hola",
                )
            )
            second = evaluator.evaluate_turn(
                TurnInput(
                    session_id="demo-summary-1",
                    caller_id="front-door",
                    transcript="me estan esperando",
                )
            )

        self.assertIn("Contexto previo:", second["model_guidance"]["prompt"])
        self.assertIn("visitor: hola", second["model_guidance"]["prompt"])
        self.assertIn("matia: Hola. A que residente vienes a ver?", second["model_guidance"]["prompt"])
