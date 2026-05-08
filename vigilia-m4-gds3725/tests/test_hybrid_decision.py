import unittest

from services.decision.hybrid import evaluate_hybrid_decision
from services.decision.model_backend import DecisionModelBackend, EchoModelBackend, ModelResponse, OllamaModelBackend
from services.decision.resident_directory import ResidentDirectory


class VerboseModelBackend(DecisionModelBackend):
    def generate_follow_up(self, prompt: str) -> ModelResponse:
        return ModelResponse(
            backend="verbose-model",
            generated_text=(
                "Contexto previo: visitante saludo. Responde en espanol claro. "
                "Solicita de forma breve a que residente o departamento viene. "
                "Explica la politica interna y reitera el prompt completo."
            ),
            prompt_used=prompt,
        )


class HybridDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_hybrid_decision_enables_model_guidance_when_follow_up_exists(self) -> None:
        result = evaluate_hybrid_decision("hola", self.directory)
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertEqual(result["decision"]["next_step"], "clarify_resident")
        self.assertEqual(result["model_guidance"]["backend"], "stub-model")
        self.assertTrue(result["model_guidance"]["generated_text"])

    def test_hybrid_decision_requests_resident_for_authorization_claim_without_department(self) -> None:
        result = evaluate_hybrid_decision("abre por favor, me estan esperando", self.directory)
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertEqual(result["decision"]["action"], "clarify_resident")
        self.assertEqual(result["decision"]["reason"], "authorization_claim_without_resident")
        self.assertTrue(result["model_guidance"]["generated_text"])

    def test_hybrid_decision_can_use_explicit_backend(self) -> None:
        result = evaluate_hybrid_decision(
            "hola",
            self.directory,
            model_backend=EchoModelBackend(),
        )
        self.assertEqual(result["model_guidance"]["backend"], "echo-model")
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Hola. A que residente vienes a ver?",
        )

    def test_hybrid_decision_can_use_ollama_backend_with_fallback(self) -> None:
        result = evaluate_hybrid_decision(
            "hola",
            self.directory,
            model_backend=OllamaModelBackend(model_name="vigilia-mini", timeout_seconds=0.001),
        )
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertIn(result["model_guidance"]["backend"], {"ollama-fallback-stub", "ollama:vigilia-mini"})

    def test_hybrid_decision_sanitizes_echo_like_or_verbose_follow_up(self) -> None:
        result = evaluate_hybrid_decision(
            "hola",
            self.directory,
            model_backend=VerboseModelBackend(),
        )

        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Hola. A que residente vienes a ver?",
        )

    def test_hybrid_decision_stub_follow_up_stays_brief_for_face_no_match(self) -> None:
        result = evaluate_hybrid_decision(
            "hola",
            self.directory,
            face_recognition_result="no_match",
        )

        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "No reconozco tu rostro. Dime a que residente o departamento vienes.",
        )

    def test_hybrid_decision_delivery_follow_up_uses_delivery_style(self) -> None:
        result = evaluate_hybrid_decision(
            "traigo un paquete",
            self.directory,
        )

        self.assertEqual(result["decision"]["action"], "clarify_delivery_recipient")
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Indica para que residente o departamento es la entrega.",
        )

    def test_hybrid_decision_urgent_follow_up_uses_urgent_style(self) -> None:
        result = evaluate_hybrid_decision(
            "urgente necesito ayuda",
            self.directory,
        )

        self.assertEqual(result["decision"]["action"], "escalate_urgent")
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Entendido. Voy a derivar la situacion urgente de inmediato.",
        )

    def test_hybrid_decision_confirmation_follow_up_uses_waiting_style(self) -> None:
        result = evaluate_hybrid_decision(
            "abre por favor donde Alvaro",
            self.directory,
        )

        self.assertEqual(result["decision"]["action"], "request_resident_confirmation")
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Un momento. Voy a confirmar con Alvaro.",
        )

    def test_hybrid_decision_authorization_follow_up_can_name_known_resident(self) -> None:
        result = evaluate_hybrid_decision(
            "abre por favor para Carlos",
            None,
        )

        self.assertEqual(result["decision"]["action"], "clarify_authorization")
        self.assertEqual(
            result["model_guidance"]["generated_text"],
            "Indica si vienes donde Carlos o quien autorizo tu ingreso.",
        )


if __name__ == "__main__":
    unittest.main()
