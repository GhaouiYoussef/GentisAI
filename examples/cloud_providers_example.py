import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from gentis_ai import Expert, Flow, Router
from gentis_ai.config import load_environment
from gentis_ai.llm import AzureOpenAILLM, BedrockLLM, OpenAICompatibleLLM, VLLMLLM

environment = load_environment()

def build_llm(provider: str):
    if provider == "azure":
        return AzureOpenAILLM(
            environment=environment,
            timeout=45.0,
            max_completion_tokens=900,
        )

    if provider == "aws":
        return BedrockLLM(
            model_name=environment.get("AWS_BEDROCK_MODEL_ID"),
            region_name=environment.get("AWS_REGION"),
            temperature=0.2,
            max_tokens=512,
        )

    if provider == "vllm":
        return VLLMLLM(
            model_name=environment.get("VLLM_MODEL", "facebook/opt-125m"),
            base_url=environment.get("VLLM_BASE_URL", "http://localhost:8000/v1"),
            api_key=environment.get("VLLM_API_KEY", "EMPTY"),
            temperature=0.2,
        )

    return OpenAICompatibleLLM(
        model_name=environment.get("OPENAI_MODEL", "gpt-4o-mini"),
        api_key=environment.get("OPENAI_API_KEY"),
        base_url=environment.get("OPENAI_BASE_URL"),
        temperature=0.2,
    )


provider = environment.get("GENTIS_PROVIDER", "azure").lower()
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
