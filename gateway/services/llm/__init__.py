"""LLM module with LangChain integration and Phoenix observability.

Provides:
- xAI (Grok) adapter for LangChain
- RAG chain with Knowledge Archive integration
- Phoenix tracing for all LLM calls
"""

from gateway.services.llm.rag_chain import (
    RAGChain,
    create_rag_chain,
)
from gateway.services.llm.xai_langchain import (
    XAIChatModel,
    get_xai_chat_model,
)

__all__ = [
    "get_xai_chat_model",
    "XAIChatModel",
    "create_rag_chain",
    "RAGChain",
]
