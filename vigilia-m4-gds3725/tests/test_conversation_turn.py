import tempfile
import unittest

from services.decision.conversation_store import ConversationStore
from services.decision.resident_directory import ResidentDirectory
from services.telephony.call_router import CallRouter
from services.telephony.in_memory import InMemorySessionFactory


class ConversationTurnTests(unittest.TestCase):
    def setUp(self) -> None:
        self.directory = ResidentDirectory.from_yaml_like_file("config/residents.example.yaml")

    def test_follow_up_turn_increments_history(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConversationStore(tmpdir)
            router = CallRouter(resident_directory=self.directory, conversation_store=store)
            factory = InMemorySessionFactory()

            first = factory.create(caller_id="gds-front-door", transcript="hola", session_id="demo-1")
            second = factory.create(
                caller_id="gds-front-door",
                transcript="vengo donde Alvaro",
                session_id="demo-1",
                prior_turn_count=1,
            )

            first_result = router.route(first)
            second_result = router.route(second)

        self.assertEqual(first_result["conversation_state"]["turn_count"], 2)
        self.assertEqual(second_result["conversation_state"]["turn_count"], 4)
        self.assertEqual(second_result["decision"]["resident_hint"], "Alvaro")


if __name__ == "__main__":
    unittest.main()
