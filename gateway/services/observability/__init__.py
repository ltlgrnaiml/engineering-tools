"""Observability module for LLM tracing and debugging.

Uses Phoenix (Arize) for local observability.
TODO: Migrate to Langfuse for production team features.
"""

from gateway.services.observability.phoenix_tracer import (
    get_tracer,
    init_phoenix,
    shutdown_phoenix,
)

__all__ = ["init_phoenix", "get_tracer", "shutdown_phoenix"]
