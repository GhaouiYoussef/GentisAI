import os
import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import json
from gentis_ai import Expert, Router, Flow
from gentis_ai.llm import OllamaLLM, GeminiLLM

# --- Define Tools ---

def get_weather(city: str) -> str:
    """
    Get the current weather for a given city.
    
    Args:
        city: The name of the city (e.g., "Paris", "New York").
    """
    # Mock data
    weather_data = {
        "paris": "Sunny, 25°C",
        "new york": "Cloudy, 18°C",
        "london": "Rainy, 15°C",
        "tokyo": "Clear, 22°C"
    }
    return weather_data.get(city.lower(), "Unknown weather for this location.")

def calculate_shipping(weight: float, destination: str) -> str:
    """
    Calculate shipping cost based on weight and destination.
    
    Args:
        weight: The weight of the package in kg.
        destination: The destination country code (e.g., "US", "FR").
    """
    base_rate = 10
    if destination.upper() == "US":
        cost = base_rate + (weight * 2)
    elif destination.upper() == "FR":
        cost = base_rate + (weight * 1.5)
    else:
        cost = base_rate + (weight * 5)
    
    return f"${cost:.2f}"

# --- Setup LLM ---

# Option 1: Use Ollama (Local)
# Ensure you have a model that supports tools (e.g., llama3, mistral)
llm = OllamaLLM(
    model_name="granite4:micro", # llama3.1 has good tool support
    host="http://localhost:11434"
)

# Option 2: Use Gemini (Cloud)
# llm = GeminiLLM(
#     model_name="gemini-2.0-flash",
#     api_key=os.getenv("GOOGLE_API_KEY")
# )

# --- Define Experts with Tools ---

# Sales expert has access to shipping calculator
sales_expert = Expert(
    name="sales",
    description="Handles sales inquiries, pricing, and shipping calculations.",
    system_prompt="You are a sales representative. You can calculate shipping costs for customers.",
    tools=[calculate_shipping]
)

# Support expert has access to weather (just for fun/demo)
support_expert = Expert(
    name="support",
    description="Handles technical support and general queries.",
    system_prompt="You are a helpful assistant. You can check the weather if asked.",
    tools=[get_weather]
)

# --- Setup Router & Flow ---

router = Router(
    experts=[sales_expert, support_expert],
    llm=llm
)

flow = Flow(router=router, llm=llm)

# --- Run Conversation ---

def run_turn(user_input):
    print(f"\nUser: {user_input}")
    try:
        response = flow.process_turn(user_input)
        print(f"Agent ({response.agent_name}): {response.content}")
        # Note: In a real implementation, the LLM might return a tool call request.
        # The current BaseLLM.generate implementation in gentis_ai returns a string.
        # For Gemini/Ollama clients, if they execute tools automatically, the final response will be text.
        # If they return a tool call object, we might need to handle it.
        # 
        # Gemini's 'automatic_function_calling' config handles the loop internally.
        # Ollama's python client does NOT handle the loop automatically yet in the simple 'chat' method 
        # unless we implement the loop.
        
    except Exception as e:
        print(f"Error: {e}")

print("--- Starting Tool Use Demo ---")

# 1. Ask about shipping (Sales Expert)
run_turn("How much to ship a 5kg package to France?")

# 2. Ask about weather (Support Expert)
run_turn("What is the weather like in Paris?")
