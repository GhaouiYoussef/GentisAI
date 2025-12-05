import unittest
from aghenticMinds.memory import PNNet
from aghenticMinds.types import Message

class TestPNNet(unittest.TestCase):
    def test_prune(self):
        history = [Message(role="user", content=f"msg {i}") for i in range(50)]
        pruned = PNNet.prune(history, max_turns=10)
        self.assertEqual(len(pruned), 20)
        self.assertEqual(pruned[-1].content, "msg 49")

    def test_sanitize_for_switch(self):
        history = [
            Message(role="system", content="Old system prompt"),
            Message(role="user", content="Hello"),
            Message(role="model", content="Context hints: some hints"),
            Message(role="model", content="Hi there"),
            Message(role="system", content="Previous conversation summary: summary"),
        ]
        sanitized = PNNet.sanitize_for_switch(history)
        
        # Should remove "Old system prompt" and "Context hints"
        # Should keep "Previous conversation summary"
        self.assertEqual(len(sanitized), 3)
        self.assertEqual(sanitized[0].content, "Hello")
        self.assertEqual(sanitized[1].content, "Hi there")
        self.assertEqual(sanitized[2].content, "Previous conversation summary: summary")

if __name__ == '__main__':
    unittest.main()
