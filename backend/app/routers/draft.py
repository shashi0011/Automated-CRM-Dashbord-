from fastapi import APIRouter, HTTPException
from app.agent import draft_store
from app.agent.tools import build_tools

router = APIRouter(prefix="/api/draft", tags=["Draft (AI-controlled form)"])


@router.get("/{session_id}")
def get_draft(session_id: str):
    return draft_store.get_draft(session_id)


@router.post("/{session_id}/submit")
def submit_draft(session_id: str):
    """Manual 'Submit' button on the left panel — persists the current
    AI-filled draft exactly like the chat-driven `submit_interaction` tool
    does (same underlying function), for reps who'd rather click than type
    'submit it'.
    """
    tools = build_tools(session_id)
    submit_tool = next(t for t in tools if t.name == "submit_interaction")
    result = submit_tool.invoke({})
    import json
    parsed = json.loads(result)
    if "error" in parsed:
        raise HTTPException(400, parsed["error"])
    return parsed


@router.delete("/{session_id}")
def reset_draft(session_id: str):
    return draft_store.reset_draft(session_id)
