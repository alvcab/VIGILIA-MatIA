import tempfile
import unittest
from pathlib import Path

from services.decision.conversation import ConversationState, ConversationTurn
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
            )
            store.save(state)

            loaded = store.load("demo-1")

        self.assertEqual(loaded.session_id, "demo-1")
        self.assertEqual(loaded.turn_count, 1)
        self.assertEqual(loaded.turns[0].text, "hola")
