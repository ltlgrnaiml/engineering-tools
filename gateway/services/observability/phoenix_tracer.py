"""Phoenix Tracer - Local LLM Observability.

Provides OpenTelemetry-based tracing for LangChain/LangGraph calls.
Phoenix UI available at http://localhost:6006 when server is running.

Usage:
    from gateway.services.observability import init_phoenix
    
    # Initialize at app startup
    init_phoenix()
    
    # All LangChain calls are now automatically traced
"""

import os
import logging
from typing import Any
from contextlib import contextmanager

logger = logging.getLogger(__name__)

# Global state
_phoenix_session = None
_tracer_provider = None


def init_phoenix(
    project_name: str = "engineering-tools",
    endpoint: str | None = None,
) -> bool:
    """Initialize Phoenix tracing.
    
    Args:
        project_name: Name for the Phoenix project/workspace.
        endpoint: Phoenix collector endpoint. If None, starts local server.
        
    Returns:
        True if initialization succeeded, False otherwise.
    """
    global _phoenix_session, _tracer_provider
    
    if _tracer_provider is not None:
        logger.info("Phoenix already initialized")
        return True
    
    try:
        import phoenix as px
        from phoenix.otel import register
        from openinference.instrumentation.langchain import LangChainInstrumentor
        
        # Start Phoenix server if no endpoint provided
        if endpoint is None:
            # Launch Phoenix in background
            _phoenix_session = px.launch_app()
            endpoint = "http://localhost:6006/v1/traces"
            logger.info(f"Phoenix UI available at: http://localhost:6006")
        
        # Register OpenTelemetry tracer
        _tracer_provider = register(
            project_name=project_name,
            endpoint=endpoint,
        )
        
        # Instrument LangChain
        LangChainInstrumentor().instrument(tracer_provider=_tracer_provider)
        
        logger.info(f"Phoenix tracing initialized for project: {project_name}")
        return True
        
    except ImportError as e:
        logger.warning(f"Phoenix not installed, tracing disabled: {e}")
        logger.info("Install with: pip install arize-phoenix arize-phoenix-otel openinference-instrumentation-langchain")
        return False
    except Exception as e:
        logger.error(f"Failed to initialize Phoenix: {e}")
        return False


def get_tracer():
    """Get the current tracer provider.
    
    Returns:
        The OpenTelemetry tracer provider, or None if not initialized.
    """
    return _tracer_provider


def shutdown_phoenix():
    """Shutdown Phoenix tracing gracefully."""
    global _phoenix_session, _tracer_provider
    
    if _tracer_provider is not None:
        try:
            from opentelemetry import trace
            if hasattr(_tracer_provider, 'shutdown'):
                _tracer_provider.shutdown()
        except Exception as e:
            logger.warning(f"Error shutting down tracer: {e}")
        _tracer_provider = None
    
    if _phoenix_session is not None:
        try:
            _phoenix_session.close()
        except Exception as e:
            logger.warning(f"Error closing Phoenix session: {e}")
        _phoenix_session = None
    
    logger.info("Phoenix tracing shutdown complete")


@contextmanager
def trace_span(name: str, attributes: dict[str, Any] | None = None):
    """Create a custom trace span.
    
    Args:
        name: Name of the span.
        attributes: Optional attributes to attach to the span.
        
    Yields:
        The span object.
        
    Example:
        with trace_span("my_operation", {"doc_id": "123"}) as span:
            result = do_something()
            span.set_attribute("result_size", len(result))
    """
    try:
        from opentelemetry import trace
        tracer = trace.get_tracer(__name__)
        
        with tracer.start_as_current_span(name) as span:
            if attributes:
                for key, value in attributes.items():
                    span.set_attribute(key, value)
            yield span
    except ImportError:
        # No OpenTelemetry, yield a dummy context
        class DummySpan:
            def set_attribute(self, key, value): pass
            def set_status(self, status): pass
            def record_exception(self, exc): pass
        yield DummySpan()


def is_tracing_enabled() -> bool:
    """Check if tracing is currently enabled.
    
    Returns:
        True if Phoenix tracing is active.
    """
    return _tracer_provider is not None
