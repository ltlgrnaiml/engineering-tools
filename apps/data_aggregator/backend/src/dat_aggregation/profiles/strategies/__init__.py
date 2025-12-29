"""Extraction strategies for profile-driven data extraction.

Per SPEC-DAT-0012: Six extraction strategies for table definitions.
Each strategy transforms nested JSON/data structures into flat DataFrames.
"""

from .base import ExtractionStrategy, SelectConfig
from .flat_object import FlatObjectStrategy
from .headers_data import HeadersDataStrategy
from .array_of_objects import ArrayOfObjectsStrategy
from .repeat_over import RepeatOverStrategy
from .unpivot import UnpivotStrategy
from .join import JoinStrategy

__all__ = [
    "ExtractionStrategy",
    "SelectConfig",
    "FlatObjectStrategy",
    "HeadersDataStrategy",
    "ArrayOfObjectsStrategy",
    "RepeatOverStrategy",
    "UnpivotStrategy",
    "JoinStrategy",
]

# Strategy registry for dispatch
STRATEGY_REGISTRY: dict[str, type[ExtractionStrategy]] = {
    "flat_object": FlatObjectStrategy,
    "headers_data": HeadersDataStrategy,
    "array_of_objects": ArrayOfObjectsStrategy,
    "repeat_over": RepeatOverStrategy,
    "unpivot": UnpivotStrategy,
    "join": JoinStrategy,
}


def get_strategy(strategy_name: str) -> ExtractionStrategy:
    """Get strategy instance by name.
    
    Args:
        strategy_name: Name of the strategy (e.g., 'flat_object', 'headers_data')
        
    Returns:
        Instantiated strategy object
        
    Raises:
        ValueError: If strategy name is unknown
    """
    if strategy_name not in STRATEGY_REGISTRY:
        raise ValueError(
            f"Unknown strategy: {strategy_name}. "
            f"Available: {list(STRATEGY_REGISTRY.keys())}"
        )
    return STRATEGY_REGISTRY[strategy_name]()
