"""Offline replies grounded in executed demo tools rather than canned successes."""

import json

from gentis_ai.llm import MockLLM


class RescueMockLLM(MockLLM):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.tools_by_prompt = {}

    def generate(self, messages, system_prompt=None, tools=None, stream=False, **kwargs):
        latest = messages[-1] if messages else None
        content = latest.content if latest else ""
        metadata = latest.metadata if latest else {}
        if metadata.get("phase") == "routing":
            return super().generate(messages, system_prompt, tools, stream, **kwargs)

        results = metadata.get("tool_results", [])
        assigned = self.tools_by_prompt.get(system_prompt, ())
        lines = []
        if metadata.get("phase") == "synthesis":
            lines.extend(metadata["expert_opinions"])
        else:
            for result in results:
                name = result["name"]
                if name not in assigned:
                    continue
                if not result["ok"]:
                    lines.append(f"{name} failed; no successful action was confirmed.")
                    continue
                output = result["output"]
                if name == "create_support_ticket":
                    lines.append(f"Created demo ticket {output['ticket_id']} for: {output['issue']}")
                elif name == "lookup_account":
                    lines.append(output["customer"])
                else:
                    lines.append(f"{name}: {json.dumps(output)}")
            if "create_support_ticket" not in assigned:
                lines.append("I cannot create tickets because create_support_ticket is not assigned to this agent.")
        reply = "\n\n".join(lines) or "No demo tools ran for this request."
        prompt_tokens = self.count_tokens((system_prompt or "") + content)
        completion_tokens = self.count_tokens(reply)
        self._last_usage = {
            "prompt_tokens": prompt_tokens,
            "completion_tokens": completion_tokens,
            "total": prompt_tokens + completion_tokens,
        }
        return (chunk for chunk in [reply]) if stream else reply
