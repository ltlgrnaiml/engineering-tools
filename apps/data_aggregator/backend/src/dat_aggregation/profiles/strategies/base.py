"""Base protocol and types for extraction strategies.

Per SPEC-DAT-0012: Defines the ExtractionStrategy protocol that all
strategies must implement.
"""

from dataclasses import dataclass, field
from typing import Any, Protocol

import polars as pl


@dataclass
class RepeatOverConfig:
    """Configuration for repeat_over iteration.
    
    Per SPEC-DAT-0012: Defines how to iterate over arrays and inject context.
    """
    path: str
    as_var: str
    inject_fields: dict[str, str] = field(default_factory=dict)


@dataclass
class JoinConfig:
    """Configuration for join operations.
    
    Per SPEC-DAT-0012: Defines left/right sources and join keys.
    """
    path: str
    key: str


@dataclass
class SelectConfig:
    """Configuration for table selection/extraction.
    
    Per SPEC-DAT-0011: Defines how to extract data from a source.
    """
    strategy: str
    path: str
    headers_key: str | None = None
    data_key: str | None = None
    repeat_over: RepeatOverConfig | None = None
    fields: list[str] | None = None
    flatten_nested: bool = False
    flatten_separator: str = "_"
    infer_headers: bool = False
    default_headers: list[str] | None = None
    id_vars: list[str] | None = None
    value_vars: list[str] | None = None
    var_name: str = "variable"
    value_name: str = "value"
    left: JoinConfig | None = None
    right: JoinConfig | None = None
    how: str = "left"


class ExtractionStrategy(Protocol):
    """Protocol for extraction strategies per SPEC-DAT-0012.
    
    Each strategy transforms nested data structures into flat DataFrames.
    """
    
    def extract(
        self,
        data: Any,
        config: SelectConfig,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Execute extraction and return DataFrame.
        
        Args:
            data: Source data (typically parsed JSON)
            config: Selection configuration from profile
            context: Context dictionary for column injection
            
        Returns:
            Extracted data as a Polars DataFrame
        """
        ...
    
    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate configuration, return list of errors.
        
        Args:
            config: Selection configuration to validate
            
        Returns:
            List of error messages (empty if valid)
        """
        ...
