"""Domain Configuration Service.

Loads, validates, and provides cached access to the domain configuration.
"""

import logging
from functools import lru_cache
from pathlib import Path
from typing import Any

import yaml

from apps.pptx_generator.backend.models.domain_config import DomainConfig, JobContext

logger = logging.getLogger(__name__)


class ConfigurationError(Exception):
    """Raised when configuration loading or validation fails."""

    pass


def _find_config_path() -> Path:
    """Find the configuration file path.

    Tries multiple locations to find the config file.

    Returns:
        Path to the configuration file.

    Raises:
        ConfigurationError: If config file not found in any location.
    """
    # Get the absolute path to the pptx_generator app directory
    app_root = Path(__file__).parent.parent.parent.resolve()

    candidates = [
        app_root / "config" / "example_config_production.yaml",
        app_root / "config" / "custom_config.yaml",
        Path("config/example_config_production.yaml"),
        Path("../config/example_config_production.yaml"),
    ]

    for path in candidates:
        if path.exists():
            logger.info(f"Found config file at: {path}")
            return path.resolve()

    raise ConfigurationError(
        f"Configuration file not found. Searched: {[str(p) for p in candidates]}"
    )


def _migrate_legacy_config(raw_config: dict[str, Any]) -> dict[str, Any]:
    """Migrate legacy config formats to current structure.

    Handles backward compatibility conversions:
    - Single job_context → job_contexts list

    Args:
        raw_config: Raw YAML config dict.

    Returns:
        Migrated config dict.
    """
    # Convert single job_context to job_contexts list
    if "job_context" in raw_config and "job_contexts" not in raw_config:
        logger.info("Migrating legacy job_context to job_contexts list")
        job_context = raw_config.pop("job_context")
        raw_config["job_contexts"] = [job_context]
        if "primary_job_context" not in raw_config:
            raw_config["primary_job_context"] = job_context.get("key", "side")

    return raw_config


@lru_cache(maxsize=1)
def load_domain_config(config_path: str | None = None) -> DomainConfig:
    """Load and validate domain configuration from YAML file.

    Args:
        config_path: Optional path to config file. If None, auto-discovers.

    Returns:
        Validated DomainConfig instance.

    Raises:
        ConfigurationError: If file not found or validation fails.
    """
    if config_path:
        path = Path(config_path)
        if not path.exists():
            raise ConfigurationError(f"Configuration file not found: {config_path}")
    else:
        path = _find_config_path()

    logger.info(f"Loading domain configuration from: {path}")

    try:
        with path.open(encoding="utf-8") as f:
            raw_config = yaml.safe_load(f)
    except yaml.YAMLError as e:
        raise ConfigurationError(f"Invalid YAML in config file: {e}") from e
    except Exception as e:
        raise ConfigurationError(f"Failed to read config file: {e}") from e

    if not raw_config:
        raise ConfigurationError("Configuration file is empty")

    # Apply migrations for backward compatibility
    raw_config = _migrate_legacy_config(raw_config)

    try:
        config = DomainConfig(**raw_config)
    except Exception as e:
        raise ConfigurationError(f"Configuration validation failed: {e}") from e

    # Log successful load
    logger.info(
        f"Domain configuration loaded successfully: "
        f"{len(config.job_contexts)} job contexts, "
        f"{len(config.metrics.canonical)} canonical metrics, "
        f"{len(config.shape_naming.filter_shorthands)} filter shorthands"
    )

    return config


def get_domain_config() -> DomainConfig:
    """Get the cached domain configuration.

    Convenience function that loads config if not already cached.

    Returns:
        Cached DomainConfig instance.
    """
    return load_domain_config()


def reload_domain_config() -> DomainConfig:
    """Reload domain configuration, clearing cache.

    Useful for testing or hot-reload scenarios.

    Returns:
        Fresh DomainConfig instance.
    """
    load_domain_config.cache_clear()
    return load_domain_config()


def get_job_context(key: str) -> JobContext | None:
    """Get a specific job context by key.

    Args:
        key: Job context key (e.g., 'side', 'wafer').

    Returns:
        JobContext if found, None otherwise.
    """
    config = get_domain_config()
    return config.get_job_context(key)


def get_primary_job_context() -> JobContext | None:
    """Get the primary job context.

    Returns:
        Primary JobContext if configured, None otherwise.
    """
    config = get_domain_config()
    return config.get_primary_job_context()
