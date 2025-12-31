"""LLM Service - xAI (Grok) integration for artifact generation.

This service provides structured output generation using the xAI API.
Includes validation, retry logic, and health checking.
"""

import json
import os
import logging
from typing import Any, TypeVar
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

import httpx
from pydantic import BaseModel, ValidationError

# Load .env file if it exists
try:
    from dotenv import load_dotenv
    env_path = Path(__file__).parent.parent.parent / ".env"
    if env_path.exists():
        load_dotenv(env_path)
except ImportError:
    pass  # dotenv not installed, rely on system env vars

logger = logging.getLogger(__name__)

# =============================================================================
# Configuration
# =============================================================================

XAI_API_KEY = os.getenv("XAI_API_KEY", "")
XAI_BASE_URL = os.getenv("XAI_BASE_URL", "https://api.x.ai/v1")
XAI_DEFAULT_MODEL = os.getenv("XAI_MODEL", "grok-4-fast-reasoning")
XAI_TIMEOUT = int(os.getenv("XAI_TIMEOUT", "60"))
XAI_MAX_RETRIES = int(os.getenv("XAI_MAX_RETRIES", "3"))

# Currently selected model (can be changed at runtime)
_current_model: str = XAI_DEFAULT_MODEL


@dataclass
class ModelInfo:
    """Information about an available model."""
    id: str
    name: str
    context_window: int
    tpm: int | None  # Tokens per minute
    rpm: int  # Requests per minute
    input_price: float  # Per million tokens
    output_price: float  # Per million tokens
    category: str
    reasoning: bool = False


# Available xAI models from console
AVAILABLE_MODELS: list[ModelInfo] = [
    # Fast reasoning models (recommended for structured output)
    ModelInfo(
        id="grok-4-1-fast-reasoning",
        name="Grok 4.1 Fast (Reasoning)",
        context_window=2_000_000,
        tpm=4_000_000,
        rpm=480,
        input_price=0.20,
        output_price=0.50,
        category="fast",
        reasoning=True,
    ),
    ModelInfo(
        id="grok-4-fast-reasoning",
        name="Grok 4 Fast (Reasoning)",
        context_window=2_000_000,
        tpm=4_000_000,
        rpm=480,
        input_price=0.20,
        output_price=0.50,
        category="fast",
        reasoning=True,
    ),
    # Fast non-reasoning models (cheaper, good for simple tasks)
    ModelInfo(
        id="grok-4-1-fast-non-reasoning",
        name="Grok 4.1 Fast",
        context_window=2_000_000,
        tpm=4_000_000,
        rpm=480,
        input_price=0.20,
        output_price=0.50,
        category="fast",
        reasoning=False,
    ),
    ModelInfo(
        id="grok-4-fast-non-reasoning",
        name="Grok 4 Fast",
        context_window=2_000_000,
        tpm=4_000_000,
        rpm=480,
        input_price=0.20,
        output_price=0.50,
        category="fast",
        reasoning=False,
    ),
    # Code-optimized model
    ModelInfo(
        id="grok-code-fast-1",
        name="Grok Code Fast",
        context_window=256_000,
        tpm=2_000_000,
        rpm=480,
        input_price=0.20,
        output_price=1.50,
        category="code",
        reasoning=False,
    ),
    # Premium models (more expensive but higher quality)
    ModelInfo(
        id="grok-4-0709",
        name="Grok 4 (Premium)",
        context_window=256_000,
        tpm=2_000_000,
        rpm=480,
        input_price=3.00,
        output_price=15.00,
        category="premium",
        reasoning=False,
    ),
    ModelInfo(
        id="grok-3",
        name="Grok 3 (Premium)",
        context_window=131_072,
        tpm=None,
        rpm=600,
        input_price=3.00,
        output_price=15.00,
        category="premium",
        reasoning=False,
    ),
    # Budget model
    ModelInfo(
        id="grok-3-mini",
        name="Grok 3 Mini",
        context_window=131_072,
        tpm=None,
        rpm=480,
        input_price=0.30,
        output_price=0.50,
        category="budget",
        reasoning=False,
    ),
    # Vision model
    ModelInfo(
        id="grok-2-vision-1212",
        name="Grok 2 Vision",
        context_window=32_768,
        tpm=None,
        rpm=600,
        input_price=2.00,
        output_price=10.00,
        category="vision",
        reasoning=False,
    ),
]

# Model lookup by ID
MODELS_BY_ID: dict[str, ModelInfo] = {m.id: m for m in AVAILABLE_MODELS}


def get_available_models() -> list[ModelInfo]:
    """Get list of available models."""
    return AVAILABLE_MODELS


def get_current_model() -> str:
    """Get the currently selected model ID."""
    return _current_model


def set_current_model(model_id: str) -> bool:
    """Set the current model.

    Args:
        model_id: The model ID to use.

    Returns:
        True if model was set, False if model ID is invalid.
    """
    global _current_model
    if model_id in MODELS_BY_ID:
        _current_model = model_id
        return True
    return False


def get_model_info(model_id: str | None = None) -> ModelInfo | None:
    """Get info for a model.

    Args:
        model_id: Model ID, or None for current model.

    Returns:
        ModelInfo or None if not found.
    """
    mid = model_id or _current_model
    return MODELS_BY_ID.get(mid)


class LLMStatus(str, Enum):
    """Status of the LLM service."""
    AVAILABLE = "available"
    UNAVAILABLE = "unavailable"
    NO_API_KEY = "no_api_key"
    RATE_LIMITED = "rate_limited"
    ERROR = "error"


@dataclass
class LLMHealthCheck:
    """Result of LLM health check."""
    status: LLMStatus
    message: str
    model: str | None = None
    rate_limit_remaining: int | None = None


@dataclass
class LLMResponse:
    """Response from LLM generation."""
    success: bool
    data: dict[str, Any] | None
    error: str | None = None
    attempts: int = 1
    raw_response: str | None = None


T = TypeVar("T", bound=BaseModel)


# =============================================================================
# Health Check
# =============================================================================

_cached_health: LLMHealthCheck | None = None


def check_health(force_refresh: bool = False) -> LLMHealthCheck:
    """Check if the xAI API is available.

    Args:
        force_refresh: Force a new health check, ignoring cache.

    Returns:
        LLMHealthCheck with status and details.
    """
    global _cached_health

    if _cached_health and not force_refresh:
        return _cached_health

    if not XAI_API_KEY:
        _cached_health = LLMHealthCheck(
            status=LLMStatus.NO_API_KEY,
            message="XAI_API_KEY environment variable not set",
        )
        return _cached_health

    try:
        with httpx.Client(timeout=10) as client:
            response = client.get(
                f"{XAI_BASE_URL}/models",
                headers={"Authorization": f"Bearer {XAI_API_KEY}"},
            )

            if response.status_code == 200:
                data = response.json()
                models = [m.get("id") for m in data.get("data", [])]
                _cached_health = LLMHealthCheck(
                    status=LLMStatus.AVAILABLE,
                    message=f"Connected. {len(models)} models available.",
                    model=XAI_DEFAULT_MODEL if XAI_DEFAULT_MODEL in models else models[0] if models else None,
                )
            elif response.status_code == 401:
                _cached_health = LLMHealthCheck(
                    status=LLMStatus.UNAVAILABLE,
                    message="Invalid API key",
                )
            elif response.status_code == 429:
                _cached_health = LLMHealthCheck(
                    status=LLMStatus.RATE_LIMITED,
                    message="Rate limited. Try again later.",
                )
            else:
                _cached_health = LLMHealthCheck(
                    status=LLMStatus.ERROR,
                    message=f"API error: {response.status_code}",
                )

    except httpx.TimeoutException:
        _cached_health = LLMHealthCheck(
            status=LLMStatus.UNAVAILABLE,
            message="Connection timeout",
        )
    except httpx.RequestError as e:
        _cached_health = LLMHealthCheck(
            status=LLMStatus.UNAVAILABLE,
            message=f"Connection error: {e}",
        )

    return _cached_health


def is_available() -> bool:
    """Quick check if LLM is available."""
    return check_health().status == LLMStatus.AVAILABLE


# =============================================================================
# Structured Output Generation
# =============================================================================

def generate_structured(
    prompt: str,
    schema: type[T],
    system_prompt: str | None = None,
    max_retries: int | None = None,
) -> LLMResponse:
    """Generate structured output matching a Pydantic schema.

    Uses JSON mode and validates response against the schema.
    Retries on validation failure with error feedback.

    Args:
        prompt: The user prompt.
        schema: Pydantic model class to validate against.
        system_prompt: Optional system prompt.
        max_retries: Max retry attempts (default from env).

    Returns:
        LLMResponse with validated data or error.
    """
    if not XAI_API_KEY:
        return LLMResponse(
            success=False,
            data=None,
            error="XAI_API_KEY not configured",
        )

    retries = max_retries or XAI_MAX_RETRIES
    attempts = 0
    last_error = None
    last_raw = None

    # Build schema description for the prompt
    schema_json = schema.model_json_schema()
    schema_str = json.dumps(schema_json, indent=2)

    # System prompt with schema enforcement
    full_system = f"""You are a structured data generator. You MUST respond with valid JSON that matches this schema:

```json
{schema_str}
```

IMPORTANT:
- Respond ONLY with valid JSON
- Do NOT include markdown code blocks or any other text
- Ensure all required fields are present
- Use appropriate data types as specified in the schema"""

    if system_prompt:
        full_system = f"{system_prompt}\n\n{full_system}"

    messages = [
        {"role": "system", "content": full_system},
        {"role": "user", "content": prompt},
    ]

    while attempts < retries:
        attempts += 1

        try:
            with httpx.Client(timeout=XAI_TIMEOUT) as client:
                response = client.post(
                    f"{XAI_BASE_URL}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {XAI_API_KEY}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "model": _current_model,
                        "messages": messages,
                        "response_format": {"type": "json_object"},
                        "temperature": 0.7,
                    },
                )

                if response.status_code == 429:
                    last_error = "Rate limited"
                    logger.warning(f"Rate limited on attempt {attempts}")
                    continue

                if response.status_code != 200:
                    last_error = f"API error: {response.status_code}"
                    logger.error(f"API error: {response.text}")
                    continue

                data = response.json()
                content = data.get("choices", [{}])[0].get("message", {}).get("content", "")
                last_raw = content

                # Parse JSON
                try:
                    parsed = json.loads(content)
                except json.JSONDecodeError as e:
                    last_error = f"Invalid JSON: {e}"
                    logger.warning(f"Invalid JSON on attempt {attempts}: {e}")
                    # Add error feedback for retry
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Your response was not valid JSON. Error: {e}. Please respond with ONLY valid JSON.",
                    })
                    continue

                # Validate against schema
                try:
                    validated = schema.model_validate(parsed)
                    return LLMResponse(
                        success=True,
                        data=validated.model_dump(),
                        attempts=attempts,
                        raw_response=content,
                    )
                except ValidationError as e:
                    last_error = f"Schema validation failed: {e}"
                    logger.warning(f"Validation failed on attempt {attempts}: {e}")
                    # Add error feedback for retry
                    messages.append({"role": "assistant", "content": content})
                    messages.append({
                        "role": "user",
                        "content": f"Your response did not match the required schema. Errors:\n{e}\n\nPlease fix and respond with valid JSON matching the schema.",
                    })
                    continue

        except httpx.TimeoutException:
            last_error = "Request timeout"
            logger.warning(f"Timeout on attempt {attempts}")
        except httpx.RequestError as e:
            last_error = f"Request error: {e}"
            logger.error(f"Request error on attempt {attempts}: {e}")

    return LLMResponse(
        success=False,
        data=None,
        error=last_error,
        attempts=attempts,
        raw_response=last_raw,
    )


def generate_text(
    prompt: str,
    system_prompt: str | None = None,
) -> LLMResponse:
    """Generate free-form text response.

    Args:
        prompt: The user prompt.
        system_prompt: Optional system prompt.

    Returns:
        LLMResponse with text in data["content"].
    """
    if not XAI_API_KEY:
        return LLMResponse(
            success=False,
            data=None,
            error="XAI_API_KEY not configured",
        )

    messages = []
    if system_prompt:
        messages.append({"role": "system", "content": system_prompt})
    messages.append({"role": "user", "content": prompt})

    try:
        with httpx.Client(timeout=XAI_TIMEOUT) as client:
            response = client.post(
                f"{XAI_BASE_URL}/chat/completions",
                headers={
                    "Authorization": f"Bearer {XAI_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": _current_model,
                    "messages": messages,
                    "temperature": 0.7,
                },
            )

            if response.status_code != 200:
                return LLMResponse(
                    success=False,
                    data=None,
                    error=f"API error: {response.status_code}",
                )

            data = response.json()
            content = data.get("choices", [{}])[0].get("message", {}).get("content", "")

            return LLMResponse(
                success=True,
                data={"content": content},
                raw_response=content,
            )

    except httpx.TimeoutException:
        return LLMResponse(success=False, data=None, error="Request timeout")
    except httpx.RequestError as e:
        return LLMResponse(success=False, data=None, error=f"Request error: {e}")


# =============================================================================
# Artifact-Specific Schemas for Structured Output
# =============================================================================

class GeneratedDiscussion(BaseModel):
    """Schema for generated Discussion content."""
    id: str
    title: str
    summary: str
    context: str
    functional_requirements: list[dict[str, str]]
    non_functional_requirements: list[dict[str, str]]
    open_questions: list[dict[str, str]]
    recommendation: str | None = None


class GeneratedADR(BaseModel):
    """Schema for generated ADR content."""
    id: str
    title: str
    status: str = "proposed"
    context: str
    decision_primary: str
    decision_details: list[str]
    consequences: list[str]
    alternatives_considered: list[dict[str, str]]
    tradeoffs: list[str] | None = None


class GeneratedSPEC(BaseModel):
    """Schema for generated SPEC content."""
    id: str
    title: str
    status: str = "draft"
    purpose: str
    scope: str
    functional_requirements: list[dict[str, str]]
    non_functional_requirements: list[dict[str, str]]
    api_endpoints: list[dict[str, str]] | None = None
    acceptance_criteria: list[str]


class GeneratedPlan(BaseModel):
    """Schema for generated Plan content."""
    id: str
    title: str
    status: str = "draft"
    objective: str
    milestones: list[dict[str, Any]]
    success_criteria: list[str]


# Map artifact types to schemas
ARTIFACT_SCHEMAS: dict[str, type[BaseModel]] = {
    "discussion": GeneratedDiscussion,
    "adr": GeneratedADR,
    "spec": GeneratedSPEC,
    "plan": GeneratedPlan,
}
