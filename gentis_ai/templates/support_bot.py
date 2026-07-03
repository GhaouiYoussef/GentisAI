from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import MockLLM

llm = MockLLM(
    routing_rules={"help": "support", "buy": "sales"},
    responses={
        "help": "I can help troubleshoot that.",
        "buy": "I can help with pricing.",
    },
)

support = Expert(name="support", description="Handles support requests.")
sales = Expert(name="sales", description="Handles sales and pricing.")

router = Router(experts=[support, sales], llm=llm)
flow = Flow(router=router, llm=llm)

response = flow.process_turn("I need help with login.", session_id="demo")
print(response.content)
