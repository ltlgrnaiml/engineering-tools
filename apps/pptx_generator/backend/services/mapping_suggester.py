"""Mapping Suggester Service.

Auto-suggests mappings between DRM requirements and data columns using:
- Exact matching
- Substring matching
- Fuzzy string matching
- Regex pattern detection
"""

import logging
import re
from difflib import SequenceMatcher

from apps.pptx_generator.backend.models.drm import DerivedRequirementsManifest
from apps.pptx_generator.backend.models.mapping_manifest import (
    MappingSourceType,
    MappingSuggestion,
)

logger = logging.getLogger(__name__)


class MappingSuggesterService:
    """Service for auto-suggesting mappings."""

    # Confidence thresholds
    EXACT_MATCH_CONFIDENCE = 1.0
    SUBSTRING_MATCH_CONFIDENCE = 0.85
    FUZZY_MATCH_MIN_CONFIDENCE = 0.5

    # Common metric name variations
    METRIC_ALIASES = {
        "cd": ["space cd", "spacecd", "space_cd"],
        "lwr": ["line lwr", "linelwr", "line_lwr", "unbiased lwr"],
        "lcdu": ["line cdu", "linecdu", "line_cdu", "local line cdu"],
        "swr": ["space swr", "spaceswr", "space_swr", "unbiased swr"],
    }

    # Regex patterns for common contexts
    CONTEXT_PATTERNS = {
        "run_key": r"DZ\d+",
        "wafer": r"W\d+",
        "die": r"D\d+",
    }

    def suggest_context_mappings(
        self,
        drm: DerivedRequirementsManifest,
        data_columns: list[str],
        config: dict | None = None,
    ) -> dict[str, MappingSuggestion]:
        """Suggest mappings for required contexts.

        Args:
            drm: Derived requirements manifest.
            data_columns: List of available data columns.
            config: Optional configuration (e.g., rename_map).

        Returns:
            Dictionary mapping context name to suggestion.
        """
        suggestions = {}
        config = config or {}

        for context in drm.required_contexts:
            context_name = context.name.lower()
            best_match = None
            best_confidence = 0.0
            best_source_type = MappingSourceType.COLUMN

            # Try exact match
            for col in data_columns:
                col_lower = col.lower()
                if col_lower == context_name:
                    best_match = col
                    best_confidence = self.EXACT_MATCH_CONFIDENCE
                    break

            # Try substring match
            if best_confidence < self.EXACT_MATCH_CONFIDENCE:
                for col in data_columns:
                    col_lower = col.lower()
                    if context_name in col_lower or col_lower in context_name:
                        confidence = self.SUBSTRING_MATCH_CONFIDENCE
                        if confidence > best_confidence:
                            best_match = col
                            best_confidence = confidence

            # Try fuzzy match
            if best_confidence < self.SUBSTRING_MATCH_CONFIDENCE:
                for col in data_columns:
                    similarity = self._calculate_similarity(context_name, col.lower())
                    if (
                        similarity > best_confidence
                        and similarity >= self.FUZZY_MATCH_MIN_CONFIDENCE
                    ):
                        best_match = col
                        best_confidence = similarity

            # Check if regex pattern detection is better
            if context_name in self.CONTEXT_PATTERNS and best_confidence < 0.9:
                # Suggest regex mapping for known patterns (only if column match isn't strong)
                best_match = self.CONTEXT_PATTERNS[context_name]
                best_confidence = 0.8
                best_source_type = MappingSourceType.REGEX

            # Create suggestion
            if best_match:
                reasoning = self._generate_reasoning(
                    context_name, best_match, best_confidence, best_source_type
                )
                suggestions[context.name] = MappingSuggestion(
                    target_name=context.name,
                    suggested_source=best_match,
                    source_type=best_source_type,
                    confidence_score=best_confidence,
                    reasoning=reasoning,
                )
            else:
                # No match found
                suggestions[context.name] = MappingSuggestion(
                    target_name=context.name,
                    suggested_source="",
                    source_type=MappingSourceType.DEFAULT,
                    confidence_score=0.0,
                    reasoning="No similar column found. Consider using default value.",
                )

        return suggestions

    def suggest_metrics_mappings(
        self,
        drm: DerivedRequirementsManifest,
        data_columns: list[str],
        config: dict | None = None,
    ) -> dict[str, MappingSuggestion]:
        """Suggest mappings for required metrics.

        Args:
            drm: Derived requirements manifest.
            data_columns: List of available data columns.
            config: Optional configuration with rename_map.

        Returns:
            Dictionary mapping metric name to suggestion.
        """
        suggestions = {}
        config = config or {}
        rename_map = config.get("rename_map", {})

        for metric in drm.required_metrics:
            metric_name = metric.name.lower()
            best_match = None
            best_confidence = 0.0

            # Try rename_map first (highest confidence)
            for col in data_columns:
                if col in rename_map and rename_map[col].lower() == metric_name:
                    best_match = col
                    best_confidence = self.EXACT_MATCH_CONFIDENCE
                    break

            # Try exact match
            if best_confidence < self.EXACT_MATCH_CONFIDENCE:
                for col in data_columns:
                    col_lower = col.lower()
                    if col_lower == metric_name:
                        best_match = col
                        best_confidence = self.EXACT_MATCH_CONFIDENCE
                        break

            # Try metric aliases
            if best_confidence < self.EXACT_MATCH_CONFIDENCE:
                aliases = self.METRIC_ALIASES.get(metric_name, [])
                for col in data_columns:
                    col_lower = col.lower()
                    for alias in aliases:
                        if alias in col_lower:
                            confidence = 0.9
                            if confidence > best_confidence:
                                best_match = col
                                best_confidence = confidence
                                break

            # Try substring match
            if best_confidence < 0.9:
                for col in data_columns:
                    col_lower = col.lower()
                    if metric_name in col_lower:
                        confidence = self.SUBSTRING_MATCH_CONFIDENCE
                        if confidence > best_confidence:
                            best_match = col
                            best_confidence = confidence

            # Try fuzzy match
            if best_confidence < self.SUBSTRING_MATCH_CONFIDENCE:
                for col in data_columns:
                    similarity = self._calculate_similarity(metric_name, col.lower())
                    if (
                        similarity > best_confidence
                        and similarity >= self.FUZZY_MATCH_MIN_CONFIDENCE
                    ):
                        best_match = col
                        best_confidence = similarity

            # Create suggestion
            if best_match:
                reasoning = self._generate_reasoning(
                    metric_name, best_match, best_confidence, MappingSourceType.COLUMN
                )
                suggestions[metric.name] = MappingSuggestion(
                    target_name=metric.name,
                    suggested_source=best_match,
                    source_type=MappingSourceType.COLUMN,
                    confidence_score=best_confidence,
                    reasoning=reasoning,
                )
            else:
                # No match found
                suggestions[metric.name] = MappingSuggestion(
                    target_name=metric.name,
                    suggested_source="",
                    source_type=MappingSourceType.COLUMN,
                    confidence_score=0.0,
                    reasoning="No similar column found. Please map manually.",
                )

        return suggestions

    def _calculate_similarity(self, str1: str, str2: str) -> float:
        """Calculate similarity ratio between two strings.

        Args:
            str1: First string.
            str2: Second string.

        Returns:
            Similarity ratio (0.0-1.0).
        """
        return SequenceMatcher(None, str1, str2).ratio()

    def _generate_reasoning(
        self,
        target: str,
        source: str,
        confidence: float,
        source_type: MappingSourceType,
    ) -> str:
        """Generate human-readable reasoning for suggestion.

        Args:
            target: Target name.
            source: Suggested source.
            confidence: Confidence score.
            source_type: Type of mapping.

        Returns:
            Reasoning string.
        """
        if confidence == self.EXACT_MATCH_CONFIDENCE:
            return f"Exact match: '{target}' -> '{source}'"
        elif confidence >= self.SUBSTRING_MATCH_CONFIDENCE:
            return f"Substring match: '{target}' found in '{source}'"
        elif source_type == MappingSourceType.REGEX:
            return f"Regex pattern suggested for '{target}': {source}"
        elif confidence >= self.FUZZY_MATCH_MIN_CONFIDENCE:
            similarity_pct = int(confidence * 100)
            return f"Fuzzy match ({similarity_pct}% similar): '{target}' -> '{source}'"
        else:
            return "Low confidence match"

    def detect_regex_pattern(self, column_values: list[str], pattern: str) -> str | None:
        """Detect if a regex pattern matches column values.

        Args:
            column_values: Sample values from column.
            pattern: Regex pattern to test.

        Returns:
            Pattern if matches found, None otherwise.
        """
        try:
            regex = re.compile(pattern)
            matches = sum(1 for val in column_values if regex.search(str(val)))
            match_ratio = matches / len(column_values) if column_values else 0

            # If pattern matches >50% of values, consider it valid
            if match_ratio > 0.5:
                return pattern
        except re.error:
            pass

        return None


# Validation test (remove after testing)
if __name__ == "__main__":
    from uuid import uuid4

    from apps.pptx_generator.backend.models.drm import (
        AggregationType,
        RequiredContext,
        RequiredMetric,
    )

    # Create test DRM
    drm = DerivedRequirementsManifest(
        template_id=uuid4(),
        required_contexts=[
            RequiredContext(name="side"),
            RequiredContext(name="wafer"),
            RequiredContext(name="run_key"),
        ],
        required_metrics=[
            RequiredMetric(name="CD", aggregation_type=AggregationType.MEAN),
            RequiredMetric(name="LWR", aggregation_type=AggregationType.SIGMA_3),
        ],
    )

    # Test data columns
    data_columns = [
        "LCDU",
        "Side",
        "Wafer",
        "CD",
        "LWR",
        "ImageColumn",
    ]

    # Test suggester
    suggester = MappingSuggesterService()

    # Test context suggestions
    context_suggestions = suggester.suggest_context_mappings(drm, data_columns)
    print("\nContext Suggestions:")
    for name, suggestion in context_suggestions.items():
        print(
            f"  {name}: {suggestion.suggested_source} (confidence: {suggestion.confidence_score:.2f})"
        )
        print(f"    Reasoning: {suggestion.reasoning}")

    # Test metrics suggestions
    config = {
        "rename_map": {
            "Space CD (nm)": "SpaceCD",
            "Unbiased LWR 3s (nm)": "LWR",
        }
    }
    metrics_suggestions = suggester.suggest_metrics_mappings(drm, data_columns, config)
    print("\nMetrics Suggestions:")
    for name, suggestion in metrics_suggestions.items():
        print(
            f"  {name}: {suggestion.suggested_source} (confidence: {suggestion.confidence_score:.2f})"
        )
        print(f"    Reasoning: {suggestion.reasoning}")

    # Assertions
    assert context_suggestions["side"].confidence_score >= 0.8
    assert context_suggestions["wafer"].confidence_score >= 0.8
    assert metrics_suggestions["CD"].confidence_score >= 0.8
    assert metrics_suggestions["LWR"].confidence_score >= 0.8

    print("\nAll mapping suggester tests passed!")
