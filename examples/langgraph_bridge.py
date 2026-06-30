import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gentis_ai import Expert, Flow, Router
from gentis_ai.adapters.langgraph import to_langgraph
from gentis_ai.llm import MockLLM

llm = MockLLM(
    routing_rules={"help": "support"},
    responses={"help": "I can help troubleshoot that."},
)

support = Expert(name="support", description="Handles support.")
router = Router(experts=[support], llm=llm)
flow = Flow(router=router, llm=llm)

graph = to_langgraph(flow)
result = graph.invoke({"input": "I need help", "session_id": "langgraph-demo"})
print(result["output"])
