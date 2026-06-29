from __future__ import annotations

from typing import Any, TypedDict


class GentisGraphState(TypedDict, total=False):
    session_id: str
    input: str
    output: str
    agent_name: str


def to_langgraph(flow: Any, checkpointer: Any = None):
    try:
        from langgraph.graph import END, StateGraph
    except ImportError as exc:
        raise ImportError(
            "LangGraph support is optional. Install it with "
            "`pip install gentis-ai[langgraph]`."
        ) from exc

    def run_turn(state: GentisGraphState) -> GentisGraphState:
        response = flow.process_turn(
            state["input"],
            session_id=state.get("session_id"),
        )
        return {
            **state,
            "output": response.content,
            "agent_name": response.agent_name,
            "session_id": response.session_id or state.get("session_id", ""),
        }

    graph = StateGraph(GentisGraphState)
    graph.add_node("gentis_turn", run_turn)
    graph.set_entry_point("gentis_turn")
    graph.add_edge("gentis_turn", END)
    return graph.compile(checkpointer=checkpointer)
