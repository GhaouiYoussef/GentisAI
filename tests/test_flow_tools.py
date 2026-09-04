import unittest

from gentis_ai import Expert, Flow, Router, ToolCall
from gentis_ai.llm import MockLLM
from gentis_ai.tools import ToolExecutor, ToolRegistry


def lookup_invoice(invoice_ref: str) -> dict[str, str]:
    return {"invoice_ref": invoice_ref, "status": "duplicate confirmed"}


class TestFlowTools(unittest.TestCase):
    def setUp(self):
        self.llm = MockLLM(
            routing_rules={"invoice": "billing"},
            responses={"invoice": "The duplicate invoice is confirmed."},
        )
        billing = Expert(name="billing", description="Billing support.")
        self.router = Router([billing], llm=self.llm, default_expert=billing)
        registry = ToolRegistry()
        registry.register(lookup_invoice)
        self.executor = ToolExecutor(registry)

    def test_flow_requires_executor_and_policy_together(self):
        with self.assertRaisesRegex(ValueError, "tool_executor and tool_policy"):
            Flow(router=self.router, llm=self.llm, tool_executor=self.executor)

    def test_stream_emits_real_tool_events(self):
        def policy(message, decision):
            return [
                ToolCall(
                    name="lookup_invoice",
                    arguments={"invoice_ref": "INV-2048"},
                )
            ]

        flow = Flow(
            router=self.router,
            llm=self.llm,
            tool_executor=self.executor,
            tool_policy=policy,
        )
        events = list(
            flow.stream_turn("Check my invoice", session_id="tool-session")
        )
        event_types = [event.type for event in events]

        self.assertLess(
            event_types.index("route_finished"),
            event_types.index("tool_call"),
        )
        self.assertLess(
            event_types.index("tool_call"),
            event_types.index("tool_result"),
        )
        result_event = next(
            event for event in events if event.type == "tool_result"
        )
        self.assertEqual(
            result_event.data["result"]["output"]["invoice_ref"],
            "INV-2048",
        )
        final = events[-1].data["response"]
        self.assertEqual(final.structured["tools"][0]["name"], "lookup_invoice")

    def test_process_and_stream_return_equivalent_results(self):
        flow = Flow(router=self.router, llm=self.llm)
        processed = flow.process_turn("Check my invoice", session_id="process")
        streamed = list(
            flow.stream_turn("Check my invoice", session_id="stream")
        )[-1].data["response"]

        self.assertEqual(processed.content.strip(), streamed.content.strip())
        self.assertEqual(processed.agent_name, streamed.agent_name)
        self.assertEqual(
            processed.structured["routing"],
            streamed.structured["routing"],
        )

    def test_tool_history_is_saved_once_without_rewriting_user_message(self):
        def policy(message, decision):
            return [
                ToolCall(
                    name="lookup_invoice",
                    arguments={"invoice_ref": "INV-2048"},
                )
            ]

        flow = Flow(
            router=self.router,
            llm=self.llm,
            tool_executor=self.executor,
            tool_policy=policy,
        )
        flow.process_turn("Check my invoice", session_id="history")
        state = flow.session_store.get("history", "billing")

        self.assertEqual(len(state.history), 2)
        self.assertEqual(state.history[0].content, "Check my invoice")

    def test_approval_result_is_emitted(self):
        executor = ToolExecutor(
            self.executor.registry,
            approval_policy={"lookup_invoice": "always"},
        )
        flow = Flow(
            router=self.router,
            llm=self.llm,
            tool_executor=executor,
            tool_policy=lambda message, decision: [
                ToolCall(
                    name="lookup_invoice",
                    arguments={"invoice_ref": "INV-2048"},
                )
            ],
        )
        result_event = next(
            event
            for event in flow.stream_turn("invoice", session_id="approval")
            if event.type == "tool_result"
        )
        self.assertTrue(result_event.data["result"]["approval_required"])

    def test_unknown_tool_emits_safe_error_and_turn_continues(self):
        flow = Flow(
            router=self.router,
            llm=self.llm,
            tool_executor=self.executor,
            tool_policy=lambda message, decision: [ToolCall(name="missing")],
        )
        events = list(flow.stream_turn("invoice", session_id="unknown"))
        error_event = next(event for event in events if event.type == "error")
        self.assertEqual(error_event.error, "Tool execution failed")
        self.assertEqual(events[-1].type, "final")


if __name__ == "__main__":
    unittest.main()
