
import datetime as dt
from typing import Annotated, TypedDict
from langgraph.graph import StateGraph, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode
from langchain_core.messages import SystemMessage

from app.agent.llm import get_llm
from app.agent.tools import build_tools

SYSTEM_PROMPT_TEMPLATE = """You are the AI Assistant panel of an AI-first pharma CRM's
HCP module. You sit next to a "Interaction Details" form that YOU control —
the rep must never type into that form directly. Your job is to fill it,
correct it, and — only when explicitly told — submit it.

Today's date is {today}.

Hard rules:
1. When the rep describes a NEW visit/call/email in natural language, call
   `log_interaction` and extract every field you can from their sentence.
2. When the rep corrects or changes something already on the form (e.g.
   "actually the name was Dr. John" or "change sentiment to negative"), call
   `edit_interaction` with ONLY the changed fields.
3. NEVER call `submit_interaction` unless the rep has explicitly asked you to
   submit/save/log it for real (e.g. "submit it", "save this", "that's right,
   log it"). Filling the form is NOT the same as submitting it — wait for
   explicit confirmation, even if all fields look complete.
4. Use `get_hcp_history` to check if an HCP already exists or to answer
   questions about past visits, before logging/submitting if useful.
5. Use `check_compliance` when the interaction involves claims, samples, or
   gifts, or if the rep asks for a compliance review.
6. Use `schedule_follow_up` when the rep mentions needing to circle back.
7. Use `suggest_next_best_action` when the rep asks what to do next with an HCP.
8. After every tool call, briefly confirm in plain language what changed on
   the form (or what was submitted). Keep replies short — this is a sidebar
   chat, not an essay.
9. Never invent facts the rep didn't say. Leave fields blank if unsure.
"""


class AgentState(TypedDict):
    messages: Annotated[list, add_messages]


_GRAPH_CACHE: dict[str, object] = {}


def _make_agent_node(tools):
    def _agent_node(state: AgentState):
        llm = get_llm().bind_tools(tools)
        messages = state["messages"]
        response = llm.invoke(messages)
        return {"messages": [response]}
    return _agent_node


def _should_continue(state: AgentState):
    last = state["messages"][-1]
    if getattr(last, "tool_calls", None):
        return "tools"
    return END


def build_graph_for_session(session_id: str):
    if session_id in _GRAPH_CACHE:
        return _GRAPH_CACHE[session_id]

    tools = build_tools(session_id)
    graph = StateGraph(AgentState)
    graph.add_node("agent", _make_agent_node(tools))
    graph.add_node("tools", ToolNode(tools))
    graph.set_entry_point("agent")
    graph.add_conditional_edges("agent", _should_continue, {"tools": "tools", END: END})
    graph.add_edge("tools", "agent")
    compiled = graph.compile()
    _GRAPH_CACHE[session_id] = compiled
    return compiled


def system_message() -> SystemMessage:
    today = dt.date.today().isoformat()
    return SystemMessage(content=SYSTEM_PROMPT_TEMPLATE.format(today=today))


def clear_session_graph(session_id: str):
    _GRAPH_CACHE.pop(session_id, None)
