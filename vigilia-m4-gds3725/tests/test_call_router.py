import unittest

from services.telephony.call_router import CallRouter
from services.telephony.in_memory import InMemorySessionFactory


class CallRouterTests(unittest.TestCase):
    def test_session_replay_open_request_routes_to_dry_run_open(self) -> None:
        session = InMemorySessionFactory().create(
            caller_id="gds-front-door",
            transcript="abre por favor",
        )

        result = CallRouter().route(session)

        self.assertEqual(result["mode"], "session-replay")
        self.assertEqual(result["decision"]["action"], "open")
        self.assertTrue(result["gate_action"]["would_open"])

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
