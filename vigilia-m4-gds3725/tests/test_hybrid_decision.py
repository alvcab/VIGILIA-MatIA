import unittest

from services.decision.hybrid import evaluate_hybrid_decision
from services.decision.model_backend import EchoModelBackend, OllamaModelBackend
from services.decision.resident_directory import ResidentDirectory


class HybridDecisionTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_hybrid_decision_enables_model_guidance_when_follow_up_exists(self) -> None:
        result = evaluate_hybrid_decision("hola", self.directory)
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertEqual(result["decision"]["next_step"], "clarify_resident")
        self.assertEqual(result["model_guidance"]["backend"], "stub-model")
        self.assertTrue(result["model_guidance"]["generated_text"])

    def test_hybrid_decision_disables_model_guidance_for_terminal_open(self) -> None:
        result = evaluate_hybrid_decision("abre por favor, me estan esperando", self.directory)
        self.assertFalse(result["model_guidance"]["enabled"])
        self.assertEqual(result["decision"]["action"], "open")
        self.assertEqual(result["model_guidance"]["generated_text"], "")

    def test_hybrid_decision_can_use_explicit_backend(self) -> None:
        result = evaluate_hybrid_decision(
            "hola",
            self.directory,
            model_backend=EchoModelBackend(),
        )
        self.assertEqual(result["model_guidance"]["backend"], "echo-model")
        self.assertTrue(result["model_guidance"]["generated_text"].startswith("[echo]"))

    def test_hybrid_decision_can_use_ollama_backend_with_fallback(self) -> None:
        result = evaluate_hybrid_decision(
            "hola",
            self.directory,
            model_backend=OllamaModelBackend(model_name="vigilia-mini", timeout_seconds=0.001),
        )
        self.assertTrue(result["model_guidance"]["enabled"])
        self.assertIn(result["model_guidance"]["backend"], {"ollama-fallback-stub", "ollama:vigilia-mini"})


if __name__ == "__main__":
    unittest.main()
