import os
from typing import Optional

try:
    # Prefer the dedicated LangChain integration if available
    from langchain_groq import ChatGroq  # type: ignore
except Exception as exc:  # pragma: no cover
    ChatGroq = None  # type: ignore


def get_groq_llm(
    model_name: str = "llama-3.1-8b-instant",
    temperature: float = 0.0,
    api_key: Optional[str] = None,
    timeout: int = 60,
):
    """
    Create and return a Groq chat LLM suitable for LangChain pipelines.

    - Requires `langchain_groq` to be installed.
    - Reads the API key from GROQ_API_KEY if not provided.
    """
    if ChatGroq is None:
        raise ImportError(
            "langchain_groq is not installed. Install with: pip install langchain-groq"
        )

    resolved_api_key = ""
    if not resolved_api_key:
        raise ValueError(
            "GROQ_API_KEY is not set. Provide api_key or set environment variable."
        )

    return ChatGroq(
        model_name=model_name,
        temperature=temperature,
        api_key=resolved_api_key,
        timeout=timeout,
    )


__all__ = ["get_groq_llm"]


