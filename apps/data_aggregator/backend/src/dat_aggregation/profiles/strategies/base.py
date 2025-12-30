"""Base protocol and types for extraction strategies.

Per SPEC-DAT-0012: Defines the ExtractionStrategy protocol that all
strategies must implement.

All contract types imported from Tier-0 shared.contracts.dat.profile.
"""

from typing import Any, Protocol

import polars as pl

from shared.contracts.dat.profile import SelectConfig

__version__ = "1.0.0"


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
            data: Source data (typically parsed JSON).
            config: Selection configuration from profile.
            context: Context dictionary for column injection.

        Returns:
            Extracted data as a Polars DataFrame.
        """
        ...

    def validate_config(self, config: SelectConfig) -> list[str]:
        """Validate configuration, return list of errors.

        Args:
            config: Selection configuration to validate.

        Returns:
            List of error messages (empty if valid).
        """
        ...
