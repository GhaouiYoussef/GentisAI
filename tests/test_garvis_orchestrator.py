import unittest
import os
from expertflow import Agent

# Helper to read files
def read_prompt(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

class TestGarvisOrchestrator(unittest.TestCase):
    def setUp(self):
        # Paths
        self.base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        self.orch_path = os.path.join(self.base_path, "expertflow", "prompts", "orchestrator", "orch.md")
        self.task_path = os.path.join(self.base_path, "expertflow", "prompts", "experts", "default", "task_planner_exp.md")
        self.msg_path = os.path.join(self.base_path, "expertflow", "prompts", "experts", "default", "msg_writer_exp.md")

        # Load Prompts
        self.orch_prompt = read_prompt(self.orch_path)
        self.task_prompt = read_prompt(self.task_path)
        self.msg_prompt = read_prompt(self.msg_path)

    def test_prompts_consistency(self):
        print("\nTesting Orchestrator Prompt Consistency...")
        # Check Orchestrator
        self.assertIn("Garvis", self.orch_prompt)
        self.assertIn("Productivity & Communication Manager", self.orch_prompt)
        self.assertIn("Task Planner", self.orch_prompt)
        self.assertIn("Message Expert", self.orch_prompt)
        print("✅ Orchestrator Prompt Verified.")
        
        print("\nTesting Task Planner Prompt Consistency...")
        # Check Task Planner
        self.assertIn("Garvis", self.task_prompt)
        self.assertIn("Task Planning Expert", self.task_prompt)
        print("✅ Task Planner Prompt Verified.")
        
        print("\nTesting Message Expert Prompt Consistency...")
        # Check Message Expert
        self.assertIn("Garvis", self.msg_prompt)
        self.assertIn("Message Expert", self.msg_prompt)
        print("✅ Message Expert Prompt Verified.")

    def test_agent_initialization(self):
        print("\nTesting Agent Initialization...")
        orch_agent = Agent(
            name="Garvis (Orchestrator)",
            system_prompt=self.orch_prompt,
            description="Strategic Orchestrator."
        )
        task_agent = Agent(
            name="Task Planner",
            system_prompt=self.task_prompt,
            description="Task Planning Expert."
        )
        msg_agent = Agent(
            name="Message Expert",
            system_prompt=self.msg_prompt,
            description="Message Writing Expert."
        )
        
        self.assertEqual(orch_agent.name, "Garvis (Orchestrator)")
        self.assertEqual(task_agent.name, "Task Planner")
        self.assertEqual(msg_agent.name, "Message Expert")
        print("✅ Agents Initialized Successfully.")

if __name__ == "__main__":
    unittest.main()
