import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gentis_ai import Expert, Flow, Router
from gentis_ai.llm import AzureOpenAILLM, BedrockLLM, OpenAICompatibleLLM, VLLMLLM


def build_llm(provider: str):
    if provider == "azure":
        return AzureOpenAILLM(
            model_name=os.getenv("AZURE_OPENAI_DEPLOYMENT"),
            azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
            api_key=os.getenv("AZURE_OPENAI_API_KEY"),
            temperature=0.2,
        )

    if provider == "aws":
        return BedrockLLM(
            model_name=os.getenv("AWS_BEDROCK_MODEL_ID"),
            region_name=os.getenv("AWS_REGION"),
            temperature=0.2,
            max_tokens=512,
        )

    if provider == "vllm":
        return VLLMLLM(
            model_name=os.getenv("VLLM_MODEL", "facebook/opt-125m"),
            base_url=os.getenv("VLLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=os.getenv("VLLM_API_KEY", "EMPTY"),
            temperature=0.2,
        )

    return OpenAICompatibleLLM(
        model_name=os.getenv("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=os.getenv("OPENAI_API_KEY"),
        base_url=os.getenv("OPENAI_BASE_URL"),
        temperature=0.2,
    )


provider = os.getenv("GENTIS_PROVIDER", "azure").lower()
llm = build_llm(provider)

support_expert = Expert(
    name="support",
    description="Handles technical support queries.",
    system_prompt="You are a technical support specialist. Help users with their issues.",
)

sales_expert = Expert(
    name="sales",
    description="Handles sales inquiries and pricing.",
    system_prompt="You are a sales representative. Answer questions about pricing and features.",
)

router = Router(experts=[support_expert, sales_expert], llm=llm)
flow = Flow(router=router, llm=llm)

response = flow.process_turn("I have a problem with my account.", session_id="cloud-demo")
print(f"Provider: {provider}")
print(f"Agent: {response.agent_name}")
print(f"Response: {response.content}")
print(f"Token Usage: {response.token_usage}")
