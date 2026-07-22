from fastapi import APIRouter
from langchain_core.messages import HumanMessage, AIMessage
from app import schemas
from app.agent.graph import build_graph_for_session, system_message, clear_session_graph
from app.agent import draft_store

router = APIRouter(prefix="/api/chat", tags=["Conversational Agent"])

# Simple in-memory per-session message history. Fine for an assignment demo;
# swap for a LangGraph checkpointer (e.g. SqliteSaver) for production.
_SESSIONS: dict[str, list] = {}


@router.post("", response_model=schemas.ChatResponse)
def chat(payload: schemas.ChatMessage):
    history = _SESSIONS.setdefault(payload.session_id, [system_message()])
    history.append(HumanMessage(content=payload.message))

    agent_app = build_graph_for_session(payload.session_id)

    try:
        result = agent_app.invoke({"messages": history})
        new_messages = result["messages"]
        _SESSIONS[payload.session_id] = new_messages
    except Exception as e:
        return schemas.ChatResponse(
            session_id=payload.session_id,
            reply=(
                "The AI agent couldn't reach the Groq LLM. Check that GROQ_API_KEY "
                f"is set correctly in backend/.env. ({e})"
            ),
            tool_calls=[],
            draft=draft_store.get_draft(payload.session_id),
        )

    tool_calls = []
    final_reply = ""
    for m in new_messages:
        if isinstance(m, AIMessage) and getattr(m, "tool_calls", None):
            for tc in m.tool_calls:
                tool_calls.append({"tool": tc["name"], "args": tc["args"]})
        if isinstance(m, AIMessage) and m.content:
            final_reply = m.content

    return schemas.ChatResponse(
        session_id=payload.session_id,
        reply=final_reply or "Done.",
        tool_calls=tool_calls,
        draft=draft_store.get_draft(payload.session_id),
    )


@router.delete("/{session_id}")
def reset_session(session_id: str):
    _SESSIONS.pop(session_id, None)
    clear_session_graph(session_id)
    draft = draft_store.reset_draft(session_id)
    return {"status": "reset", "draft": draft}
