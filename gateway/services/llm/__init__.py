"""LLM module with LangChain integration and Phoenix observability.

Provides:
- xAI (Grok) adapter for LangChain
- RAG chain with Knowledge Archive integration
- Phoenix tracing for all LLM calls
"""

from gateway.services.llm.xai_langchain import (
    get_xai_chat_model,
    XAIChatModel,
)
from gateway.services.llm.rag_chain import (
    create_rag_chain,
    RAGChain,
)

__all__ = [
    "get_xai_chat_model",
    "XAIChatModel",
    "create_rag_chain",
    "RAGChain",
]
