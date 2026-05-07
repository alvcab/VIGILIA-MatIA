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
        self.assertEqual(second["conversation_state"]["turns"][2]["text"], "vengo donde Alvaro")
        self.assertEqual(second["conversation_state"]["turns"][3]["speaker"], "matia")

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
        self.assertEqual(result["spoken_response"], "")

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
            "No reconozco tu rostro. Indica a que residente o unidad vienes.",
        )

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
            "Indica que residente o unidad autorizo tu ingreso.",
        )
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Indica que residente o unidad autorizo tu ingreso.",
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
        self.assertEqual(second["decision"]["action"], "announce_resident")
        self.assertEqual(second["decision"]["resident_hint"], "Alvaro")
        self.assertEqual(second["spoken_response"], "Entendido. Avisare a Alvaro.")

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
                    transcript="casa 1",
                )
            )

        self.assertEqual(second["decision"]["action"], "announce_resident")
        self.assertEqual(second["decision"]["resident_hint"], "Alvaro")

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
