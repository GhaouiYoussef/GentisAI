import unittest
from switchboard_ai import Agent, Router, MemoryOptimizer, Message

class TestSwitchboardAI(unittest.TestCase):
    def test_agent_creation(self):
        agent = Agent(
            name="test_agent",
            system_prompt="You are a test.",
            description="For testing purposes."
        )
        self.assertEqual(agent.name, "test_agent")
        self.assertEqual(agent.model_name, "gemini-2.0-flash")

    def test_memory_pruning(self):
        history = [Message(role="user", content=str(i)) for i in range(50)]
        pruned = MemoryOptimizer.prune(history, max_turns=10)
        self.assertEqual(len(pruned), 20) # max_turns * 2
        self.assertEqual(pruned[-1].content, "49")

    def test_memory_sanitization(self):
        history = [
            Message(role="system", content="Old Prompt"),
            Message(role="user", content="Hi"),
            Message(role="model", content="Context hints: mode=old"),
            Message(role="assistant", content="Hello")
        ]
        clean = MemoryOptimizer.sanitize_for_switch(history)
        self.assertEqual(len(clean), 2)
        self.assertEqual(clean[0].content, "Hi")
        self.assertEqual(clean[1].content, "Hello")

    def test_router_initialization(self):
        a1 = Agent(name="a1", system_prompt="p1", description="d1")
        a2 = Agent(name="a2", system_prompt="p2", description="d2")
        router = Router(agents=[a1, a2], default_agent=a1)
        
        self.assertEqual(router.get_agent("a1").name, "a1")
        self.assertEqual(router.get_agent("unknown").name, "a1") # Default

if __name__ == "__main__":
    unittest.main()
