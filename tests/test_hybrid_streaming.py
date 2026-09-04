import asyncio
import unittest

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM


class TestHybridStreaming(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLM(
            routing_rules={"combined": ["billing", "support"]},
            responses={"combined": "A coordinated answer."},
        )
        self.lead = Expert(name="lead", description="Synthesizes answers.")
        self.billing = Expert(name="billing", description="Billing.")
        self.support = Expert(name="support", description="Support.")
        self.flow = Flow(
            router=Router(
                [self.lead, self.billing, self.support],
                llm=self.llm,
                default_expert=self.lead,
            ),
            llm=self.llm,
            parallel_execution=True,
        )

    def test_hybrid_stream_emits_selected_experts_and_synthesis_tokens(self):
        events = list(
            self.flow.stream_turn("combined request", session_id="hybrid")
        )
        started = [
            event.agent_name for event in events if event.type == "expert_started"
        ]
        tokens = [event.content for event in events if event.type == "token"]

        self.assertEqual(started[:2], ["billing", "support"])
        self.assertIn("lead", started)
        self.assertTrue(tokens)
        self.assertEqual(events[-1].type, "final")
        self.assertEqual(events[-1].data["response"].agent_name, "lead")
        self.assertEqual(
            events[-1].data["response"].structured["routing"]["mode"],
            "hybrid",
        )

    def test_hybrid_history_is_updated_once_with_final_answer(self):
        self.flow.process_turn("combined request", session_id="memory")
        state = self.flow.session_store.get("memory", "lead")

        self.assertEqual(len(state.history), 2)
        self.assertEqual(state.history[0].content, "combined request")
        self.assertEqual(state.history[1].metadata["expert"], "lead")

    def test_async_stream_has_same_terminal_response(self):
        async def collect():
            return [
                event
                async for event in self.flow.astream_turn(
                    "combined request",
                    session_id="async-hybrid",
                )
            ]

        events = asyncio.run(collect())
        self.assertEqual(events[-1].type, "final")
        self.assertTrue(any(event.type == "token" for event in events))


if __name__ == "__main__":
    unittest.main()
