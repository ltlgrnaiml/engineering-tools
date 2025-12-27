"""DAT extraction profiles.

Per ADR-0011: Profiles are the single source of truth for extraction logic.
"""
from .profile_loader import (
    DATProfile,
    LevelConfig,
    TableConfig,
    TableSelect,
    ContextConfig,
    ContextDefaults,
    RegexPattern,
    OutputConfig,
    load_profile,
    load_profile_from_string,
    get_builtin_profiles,
    get_profile_by_id,
)

__all__ = [
    "DATProfile",
    "LevelConfig",
    "TableConfig",
    "TableSelect",
    "ContextConfig",
    "ContextDefaults",
    "RegexPattern",
    "OutputConfig",
    "load_profile",
    "load_profile_from_string",
    "get_builtin_profiles",
    "get_profile_by_id",
]
