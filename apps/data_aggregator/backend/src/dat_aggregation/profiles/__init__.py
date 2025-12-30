"""DAT extraction profiles.

Per ADR-0012: Profiles are the single source of truth for extraction logic.
Tier-0 contracts imported from shared.contracts.dat.profile.
"""
from shared.contracts.dat.profile import (
    AggregationConfig,
    ContentPattern,
    ContextConfig,
    ContextDefaults,
    DATProfile,
    GovernanceConfig,
    JoinConfig,
    JoinHow,
    JoinOutputConfig,
    LevelConfig,
    OnFailBehavior,
    OutputConfig,
    ProfileValidationResult,
    RegexPattern,
    RegexScope,
    RepeatOverConfig,
    SelectConfig,
    StrategyType,
    TableConfig,
    UIConfig,
)

from .profile_loader import (
    get_builtin_profiles,
    get_profile_by_id,
    load_profile,
    load_profile_from_string,
    validate_profile,
)

__all__ = [
    # Tier-0 contracts (from shared.contracts.dat.profile)
    "AggregationConfig",
    "ContentPattern",
    "ContextConfig",
    "ContextDefaults",
    "DATProfile",
    "GovernanceConfig",
    "JoinConfig",
    "JoinHow",
    "JoinOutputConfig",
    "LevelConfig",
    "OnFailBehavior",
    "OutputConfig",
    "ProfileValidationResult",
    "RegexPattern",
    "RegexScope",
    "RepeatOverConfig",
    "SelectConfig",
    "StrategyType",
    "TableConfig",
    "UIConfig",
    # Loader functions
    "get_builtin_profiles",
    "get_profile_by_id",
    "load_profile",
    "load_profile_from_string",
    "validate_profile",
]
