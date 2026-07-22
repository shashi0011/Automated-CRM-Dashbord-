from langchain_groq import ChatGroq
from app.config import settings


def get_llm(temperature: float = 0.2, model: str | None = None):
    """
    Returns a ChatGroq LLM instance.
    Defaults to gemma2-9b-it as mandated by the assignment; falls back to
    llama-3.3-70b-versatile if a heavier-context model is needed by a tool.
    """
    return ChatGroq(
        api_key=settings.groq_api_key,
        model=model or settings.groq_model,
        temperature=temperature,
    )
