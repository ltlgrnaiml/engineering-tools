"""File filter predicates for datasource filtering.

Per DESIGN §2: Supports composable file filter predicates with AND/OR/NOT logic.
"""

import logging
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class FilterPredicate:
    """Single filter predicate per DESIGN §2.
    
    Attributes:
        field: Field to filter on (filename, extension, path, size, modified_date)
        op: Comparison operator (equals, contains, startswith, endswith, matches, gt, lt)
        value: Value to compare against
        case: Case sensitivity (sensitive, insensitive)
    """
    field: str
    op: str
    value: Any
    case: str = "insensitive"


@dataclass
class FilterGroup:
    """Composable filter group per DESIGN §2.
    
    Attributes:
        op: Logical operator (AND, OR, NOT)
        children: List of FilterPredicate or FilterGroup
    """
    op: str  # AND, OR, NOT
    children: list[Any] = field(default_factory=list)


class FileFilter:
    """Evaluates file filter predicates per DESIGN §2.
    
    Supports composable predicates with AND/OR/NOT logic for file matching.
    """
    
    def matches(self, file_path: Path, filter_config: dict[str, Any]) -> bool:
        """Check if file matches filter configuration.
        
        Args:
            file_path: Path to file
            filter_config: Filter configuration from profile
            
        Returns:
            True if file matches filter
        """
        if not filter_config:
            return True  # No filter = match all
        
        filter_type = filter_config.get("type", "predicate")
        
        if filter_type == "group":
            return self._evaluate_group(file_path, filter_config)
        elif filter_type == "predicate":
            return self._evaluate_predicate(file_path, filter_config)
        else:
            logger.warning(f"Unknown filter type: {filter_type}")
            return True
    
    def _evaluate_group(self, file_path: Path, group: dict[str, Any]) -> bool:
        """Evaluate a filter group (AND/OR/NOT).
        
        Args:
            file_path: Path to file
            group: Group configuration with op and children
            
        Returns:
            Result of logical operation
        """
        op = group.get("op", "AND").upper()
        children = group.get("children", [])
        
        if not children:
            return True
        
        if op == "AND":
            return all(self.matches(file_path, child) for child in children)
        elif op == "OR":
            return any(self.matches(file_path, child) for child in children)
        elif op == "NOT":
            # NOT applies to first child only
            if children:
                return not self.matches(file_path, children[0])
            return True
        else:
            logger.warning(f"Unknown group op: {op}")
            return True
    
    def _evaluate_predicate(
        self, file_path: Path, predicate: dict[str, Any]
    ) -> bool:
        """Evaluate a single predicate.
        
        Args:
            file_path: Path to file
            predicate: Predicate configuration
            
        Returns:
            True if predicate matches
        """
        field_name = predicate.get("field", "filename")
        op = predicate.get("op", "equals")
        value = predicate.get("value")
        case = predicate.get("case", "insensitive")
        
        # Get field value
        field_value = self._get_field_value(file_path, field_name)
        if field_value is None:
            return False
        
        # Apply case sensitivity for string comparisons
        if isinstance(field_value, str) and isinstance(value, str):
            if case == "insensitive":
                field_value = field_value.lower()
                value = value.lower()
        
        # Evaluate operator
        return self._apply_operator(field_value, op, value, predicate)
    
    def _get_field_value(self, file_path: Path, field_name: str) -> Any:
        """Get field value from file path.
        
        Args:
            file_path: Path to file
            field_name: Field to extract
            
        Returns:
            Field value or None
        """
        if field_name == "filename":
            return file_path.name
        elif field_name == "extension":
            return file_path.suffix
        elif field_name == "path":
            return str(file_path.parent)
        elif field_name == "full_path":
            return str(file_path)
        elif field_name == "size":
            try:
                return file_path.stat().st_size
            except OSError:
                return None
        elif field_name == "modified_date":
            try:
                return datetime.fromtimestamp(file_path.stat().st_mtime)
            except OSError:
                return None
        else:
            logger.warning(f"Unknown field: {field_name}")
            return None
    
    def _apply_operator(
        self,
        field_value: Any,
        op: str,
        value: Any,
        predicate: dict[str, Any],
    ) -> bool:
        """Apply comparison operator.
        
        Args:
            field_value: Value from file
            op: Operator name
            value: Value to compare against
            predicate: Full predicate (for additional args)
            
        Returns:
            Comparison result
        """
        if op == "equals":
            return field_value == value
        elif op == "not_equals":
            return field_value != value
        elif op == "contains":
            return str(value) in str(field_value)
        elif op == "startswith":
            return str(field_value).startswith(str(value))
        elif op == "endswith":
            return str(field_value).endswith(str(value))
        elif op == "matches":
            try:
                return bool(re.search(str(value), str(field_value)))
            except re.error:
                return False
        elif op == "gt":
            return field_value > value
        elif op == "gte":
            return field_value >= value
        elif op == "lt":
            return field_value < value
        elif op == "lte":
            return field_value <= value
        elif op == "in":
            values = predicate.get("values", [])
            return field_value in values
        elif op == "not_in":
            values = predicate.get("values", [])
            return field_value not in values
        else:
            logger.warning(f"Unknown operator: {op}")
            return True


def filter_files(
    files: list[Path],
    filter_config: dict[str, Any],
) -> list[Path]:
    """Filter files using predicate configuration.
    
    Args:
        files: List of file paths
        filter_config: Filter configuration from profile
        
    Returns:
        Filtered list of file paths
    """
    if not filter_config:
        return files
    
    file_filter = FileFilter()
    return [f for f in files if file_filter.matches(f, filter_config)]
