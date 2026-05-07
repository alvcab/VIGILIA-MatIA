import tempfile
import unittest
from pathlib import Path

from services.decision.conversation import ConversationState, ConversationTurn, SessionMemory
from services.decision.conversation_store import ConversationStore


class ConversationStoreTests(unittest.TestCase):
    def test_store_persists_and_loads_turns(self) -> None:
        with tempfile.TemporaryDirectory() as tmpdir:
            store = ConversationStore(tmpdir)
            state = ConversationState(
                session_id="demo-1",
                turns=(
                ConversationTurn(turn_index=1, speaker="visitor", text="hola"),
                ),
                next_step="clarify_resident",
                memory=SessionMemory(
                    resident_candidate="Alvaro",
                    current_intent="visit",
                    department_target="Departamento 1",
                    department_authorization_status="pending",
                    registered_visit_expected_code="1234",
                    waiting_for_department_response=True,
                    waiting_for_visit_code=False,
                    last_next_step="await_department_response",
                ),
            )
            store.save(state)

            loaded = store.load("demo-1")

        self.assertEqual(loaded.session_id, "demo-1")
        self.assertEqual(loaded.turn_count, 1)
        self.assertEqual(loaded.turns[0].text, "hola")
        self.assertEqual(loaded.memory.resident_candidate, "Alvaro")
        self.assertEqual(loaded.memory.department_target, "Departamento 1")
        self.assertEqual(loaded.memory.department_authorization_status, "pending")
        self.assertEqual(loaded.memory.registered_visit_expected_code, "1234")
        self.assertTrue(loaded.memory.waiting_for_department_response)
