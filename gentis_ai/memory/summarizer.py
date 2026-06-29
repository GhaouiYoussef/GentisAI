from __future__ import annotations

import logging
from typing import Any

from gentis_ai.core.types import Message

logger = logging.getLogger(__name__)


class PNNet:
    """Small pruning and summarization helper for conversation history."""

    @staticmethod
    def prune(history: list[Message], max_turns: int = 20) -> list[Message]:
        if len(history) > max_turns * 2:
            return history[-(max_turns * 2) :]
        return history

    @staticmethod
    def sanitize_for_switch(history: list[Message]) -> list[Message]:
        clean_history = []
        for message in history:
            if message.role == "system":
                if message.content.startswith("Previous conversation summary:"):
                    clean_history.append(message)
                continue
            if (
                message.role == "assistant"
                and message.content.startswith("Context hints:")
            ):
                continue
            clean_history.append(message)
        return clean_history

    @staticmethod
    def summarize_if_needed(
        history: list[Message],
        llm: Any,
        token_limit: int = 500,
        target_tokens: int = 150,
    ) -> list[Message]:
        full_text = "\n".join(f"{msg.role}: {msg.content}" for msg in history)
        if hasattr(llm, "count_tokens"):
            current_tokens = llm.count_tokens(full_text)
        else:
            current_tokens = len(full_text) // 4

        if current_tokens <= token_limit or len(history) <= 4:
            return history

        messages_to_summarize = history[:-4]
        recent_messages = history[-4:]
        text_to_summarize = "\n".join(
            f"{msg.role}: {msg.content}" for msg in messages_to_summarize
        )
        prompt = (
            "Summarize the following conversation history into a concise summary "
            f"of approximately {target_tokens} tokens. Preserve key context.\n\n"
            f"{text_to_summarize}"
        )

        try:
            summary_text = llm.generate(
                messages=[Message(role="user", content=prompt)],
                system_prompt="You summarize conversation history for future turns.",
            )
            if hasattr(summary_text, "__iter__") and not isinstance(summary_text, str):
                summary_text = "".join(summary_text)
            summary = Message(
                role="system",
                content=f"Previous conversation summary: {summary_text}",
            )
            return [summary] + recent_messages
        except Exception:
            logger.exception("Summarization failed")
            return history
