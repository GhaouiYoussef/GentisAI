from gentis_ai import Expert


def build_agent(system_prompt: str) -> Expert:
    return Expert(
        name="assistant",
        description="Answers general questions and helps users get started with this project.",
        system_prompt=system_prompt,
    )
