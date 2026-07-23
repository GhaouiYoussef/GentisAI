import io
import unittest

from gentis_ai.llm import MockLLM

from app import build_flow, build_llm, stream_support_turn


class AzureSupportPOCTests(unittest.TestCase):
    def setUp(self):
        self.messages = []
        self.llm, self.provider = build_llm(
            {},
            output=self.messages.append,
        )
        self.flow = build_flow(self.llm)

    def test_runs_without_azure_credentials(self):
        self.assertIsInstance(self.llm, MockLLM)
        self.assertEqual(self.provider, "local mock")
        self.assertIn("using the local mock provider", self.messages[0])

    def test_registers_exactly_three_agents(self):
        self.assertEqual(
            set(self.flow.router.experts),
            {
                "technical_support",
                "billing_support",
                "account_support",
            },
        )

    def test_routes_billing_question(self):
        response = self.flow.process_turn(
            "I was charged twice this month.",
            session_id="generated-test",
        )
        self.assertEqual(response.agent_name, "billing_support")

    def test_streams_visible_route_and_agent(self):
        output = io.StringIO()
        ticks = iter([2.0, 2.1])

        content = stream_support_turn(
            self.flow,
            "The dashboard crashes when I upload a file.",
            stream=output,
            clock=lambda: next(ticks),
        )

        self.assertIn(
            "[route] technical_support selected in 100 ms",
            output.getvalue(),
        )
        self.assertIn("[agent] technical_support", output.getvalue())
        self.assertTrue(content)


if __name__ == "__main__":
    unittest.main()
