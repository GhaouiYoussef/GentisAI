import unittest
import tempfile
from gentis_ai.session import Flow
from gentis_ai.router import Router
from gentis_ai.types import Expert
from gentis_ai.llm.mock import MockLLM
from gentis_ai.memory import SQLiteSessionStore

class TestSession(unittest.TestCase):
    def setUp(self):
        self.experts = [
            Expert(name="orchestrator", description="General", system_prompt="sys"),
            Expert(name="sales", description="Sales expert", system_prompt="sales sys")
        ]
        self.mock_llm = MockLLM(
            responses={"hello": "Hello there!", "buy": "Sure, what do you want?"},
            routing_rules={"buy": "sales", "hello": "orchestrator"}
        )
        self.router = Router(self.experts, self.mock_llm)
        self.flow = Flow(self.router, self.mock_llm)

    def test_process_turn_no_switch(self):
        response = self.flow.process_turn("hello", user_id="user1")
        self.assertEqual(response.agent_name, "orchestrator")
        self.assertEqual(response.content, "Hello there!")
        self.assertFalse(response.switched_context)

    def test_process_turn_switch(self):
        # First turn to set context
        self.flow.process_turn("hello", user_id="user1")
        
        # Second turn triggers switch
        response = self.flow.process_turn("I want to buy", user_id="user1")
        self.assertEqual(response.agent_name, "sales")
        self.assertTrue(response.switched_context)

    def test_session_persistence(self):
        self.flow.process_turn("hello", user_id="user1")
        session = self.flow._get_session("user1")
        self.assertEqual(len(session["history"]), 2) # User + Assistant

        # New user should have empty history
        session2 = self.flow._get_session("user2")
        self.assertEqual(len(session2["history"]), 0)

    def test_anonymous_sessions_do_not_collide(self):
        first = self.flow.process_turn("hello")
        second = self.flow.process_turn("hello")
        self.assertNotEqual(first.session_id, second.session_id)

    def test_explicit_session_id(self):
        response = self.flow.process_turn("hello", session_id="session-a")
        self.assertEqual(response.session_id, "session-a")
        session = self.flow._get_session("session-a")
        self.assertEqual(len(session["history"]), 2)

    def test_stream_turn_emits_events_and_final_response(self):
        events = list(self.flow.stream_turn("hello", session_id="stream-a"))
        self.assertEqual(events[0].type, "route_started")
        self.assertIn("route_finished", [event.type for event in events])
        self.assertEqual(events[-1].type, "final")
        self.assertEqual(events[-1].data["response"].content.strip(), "Hello there!")

    def test_sqlite_store_works_with_flow_restart(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = f"{tmp}/gentis.db"
            store = SQLiteSessionStore(path)
            flow = Flow(self.router, self.mock_llm, session_store=store)
            flow.process_turn("I want to buy", session_id="persisted")
            store.close()

            reopened = SQLiteSessionStore(path)
            flow2 = Flow(self.router, self.mock_llm, session_store=reopened)
            session = flow2._get_session("persisted")
            self.assertEqual(session["current_expert"], "sales")
            self.assertEqual(len(session["history"]), 2)
            reopened.close()

if __name__ == '__main__':
    unittest.main()
