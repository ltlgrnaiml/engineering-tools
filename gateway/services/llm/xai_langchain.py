"""xAI (Grok) LangChain Adapter.

Provides a LangChain-compatible chat model that uses xAI's API.
All calls are automatically traced by Phoenix when enabled.

Usage:
    from gateway.services.llm import get_xai_chat_model
    
    llm = get_xai_chat_model()
    response = llm.invoke("Hello, how are you?")
"""

import logging
import os
from typing import Any

from langchain_openai import ChatOpenAI

logger = logging.getLogger(__name__)

# xAI Configuration (OpenAI-compatible API)
XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_DEFAULT_MODEL = os.getenv("XAI_MODEL", "grok-3-fast")


class XAIChatModel(ChatOpenAI):
    """LangChain ChatModel for xAI (Grok).
    
    This is a thin wrapper around ChatOpenAI since xAI uses
    an OpenAI-compatible API.
    
    Attributes:
        model: The Grok model to use.
        temperature: Sampling temperature (0-2).
        max_tokens: Maximum tokens in response.
    """

    def __init__(
        self,
        model: str = XAI_DEFAULT_MODEL,
        temperature: float = 0.7,
        max_tokens: int | None = None,
        api_key: str | None = None,
        base_url: str | None = None,
        **kwargs: Any,
    ):
        """Initialize xAI chat model.
        
        Args:
            model: Grok model name (e.g., 'grok-3-fast', 'grok-4-fast-reasoning').
            temperature: Sampling temperature.
            max_tokens: Maximum response tokens.
            api_key: xAI API key. Defaults to XAI_API_KEY env var.
            base_url: xAI API base URL. Defaults to XAI_BASE_URL env var.
            **kwargs: Additional ChatOpenAI arguments.
        """
        super().__init__(
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            api_key=api_key or XAI_API_KEY,
            base_url=base_url or XAI_BASE_URL,
            **kwargs,
        )


def get_xai_chat_model(
    model: str | None = None,
    temperature: float = 0.7,
    max_tokens: int | None = None,
    streaming: bool = False,
) -> XAIChatModel:
    """Get an xAI chat model instance.
    
    Args:
        model: Grok model name. Defaults to XAI_MODEL env var.
        temperature: Sampling temperature (0-2).
        max_tokens: Maximum response tokens.
        streaming: Enable streaming responses.
        
    Returns:
        Configured XAIChatModel instance.
        
    Raises:
        ValueError: If XAI_API_KEY is not set.
        
    Example:
        llm = get_xai_chat_model(model="grok-3-fast")
        response = llm.invoke("Explain RAG in one sentence.")
    """
    if not XAI_API_KEY:
        raise ValueError(
            "XAI_API_KEY environment variable is required. "
            "Get your key at https://console.x.ai/"
        )

    return XAIChatModel(
        model=model or XAI_DEFAULT_MODEL,
        temperature=temperature,
        max_tokens=max_tokens,
        streaming=streaming,
    )


# Available xAI models for reference
AVAILABLE_MODELS = {
    # Fast models (good for most tasks)
    "grok-3-fast": "Grok 3 Fast - Balanced speed/quality",
    "grok-4-fast-non-reasoning": "Grok 4 Fast - Latest fast model",
    # Reasoning models (for complex tasks)
    "grok-3-mini-fast-reasoning": "Grok 3 Mini Reasoning - Fast reasoning",
    "grok-4-fast-reasoning": "Grok 4 Fast Reasoning - Best reasoning",
    # Legacy
    "grok-2-latest": "Grok 2 - Previous generation",
}


def list_available_models() -> dict[str, str]:
    """List available xAI models.
    
    Returns:
        Dict mapping model ID to description.
    """
    return AVAILABLE_MODELS.copy()
