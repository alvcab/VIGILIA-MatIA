import unittest

from services.telephony.call_router import CallRouter
from services.telephony.in_memory import InMemorySessionFactory


class CallRouterTests(unittest.TestCase):
    def test_session_replay_open_request_requires_authorization(self) -> None:
        session = InMemorySessionFactory().create(
            caller_id="gds-front-door",
            transcript="abre por favor",
        )

        result = CallRouter().route(session)

        self.assertEqual(result["mode"], "session-replay")
        self.assertEqual(result["decision"]["action"], "clarify_authorization")
        self.assertFalse(result["gate_action"]["would_open"])

    def test_session_replay_authorization_claim_without_department_requests_resident(self) -> None:
        session = InMemorySessionFactory().create(
            caller_id="gds-front-door",
            transcript="abre por favor, me estan esperando",
        )

        result = CallRouter().route(session)

        self.assertEqual(result["decision"]["action"], "clarify_resident")
        self.assertFalse(result["gate_action"]["would_open"])

    def test_session_replay_greeting_requests_clarification(self) -> None:
        session = InMemorySessionFactory().create(
            caller_id="gds-front-door",
            transcript="hola",
        )

        result = CallRouter().route(session)

        self.assertEqual(result["decision"]["action"], "greet_and_clarify")
        self.assertEqual(
            result["spoken_response"],
            "Hola. A que residente vienes a ver?",
        )


if __name__ == "__main__":
    unittest.main()
