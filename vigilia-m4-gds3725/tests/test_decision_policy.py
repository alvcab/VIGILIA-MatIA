import unittest

from services.decision.policy import decide_from_text


class DecisionPolicyTests(unittest.TestCase):
    def test_empty_text_requests_retry(self) -> None:
        decision = decide_from_text("")
        self.assertEqual(decision.action, "ask_retry")
        self.assertFalse(decision.should_open)

    def test_open_request_opens(self) -> None:
        decision = decide_from_text("abre por favor")
        self.assertEqual(decision.action, "open")
        self.assertTrue(decision.should_open)

    def test_greeting_requires_clarification(self) -> None:
        decision = decide_from_text("hola")
        self.assertEqual(decision.action, "greet_and_clarify")
        self.assertFalse(decision.should_open)


if __name__ == "__main__":
    unittest.main()
