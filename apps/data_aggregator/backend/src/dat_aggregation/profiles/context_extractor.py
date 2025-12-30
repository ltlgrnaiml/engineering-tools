"""ContextExtractor - 4-level priority context extraction.

Per ADR-0011: Context values are resolved using a 4-level priority system:
1. User Override (highest) - Explicit user input
2. Content Patterns - JSONPath from file content
3. Regex Patterns - Regex from filename/path
4. Defaults (lowest) - Static defaults from profile
"""

import logging
import re
from datetime import datetime
from pathlib import Path
from typing import Any

from jsonpath_ng import parse as jsonpath_parse

from shared.contracts.dat.profile import (
    ContentPattern,
    DATProfile,
    RegexPattern,
)


class SkipFileException(Exception):
    """Signal that current file should be skipped due to required pattern failure."""

logger = logging.getLogger(__name__)


class ContextExtractor:
    """4-level priority context extraction per ADR-0011.
    
    Extracts context values from multiple sources and merges them
    according to priority (higher priority values override lower).
    """
    
    def extract(
        self,
        profile: DATProfile,
        file_path: Path,
        file_content: dict | None = None,
        user_overrides: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        """Extract context using 4-level priority.
        
        Args:
            profile: DATProfile with context configuration
            file_path: Path to file (for regex extraction)
            file_content: Parsed file content (for JSONPath extraction)
            user_overrides: User-provided overrides (highest priority)
            
        Returns:
            Merged context dictionary
        """
        context: dict[str, Any] = {}
        
        # Priority 4: Defaults (lowest)
        if profile.context_defaults and profile.context_defaults.defaults:
            context.update(profile.context_defaults.defaults)
            logger.debug(f"Applied {len(profile.context_defaults.defaults)} defaults")
        
        # Priority 3: Regex from filename
        if profile.context_defaults and profile.context_defaults.regex_patterns:
            regex_values = self._extract_regex(
                profile.context_defaults.regex_patterns,
                file_path,
            )
            context.update(regex_values)
            logger.debug(f"Extracted {len(regex_values)} values via regex")
        
        # Priority 2: JSONPath from content (content_patterns)
        if file_content and profile.context_defaults and profile.context_defaults.content_patterns:
            content_values = self._extract_content_patterns(
                profile.context_defaults.content_patterns,
                file_content,
            )
            context.update(content_values)
            logger.debug(f"Extracted {len(content_values)} values via content patterns")
        
        # Priority 1: User overrides (highest, allowlisted)
        if user_overrides:
            allowed = (
                profile.context_defaults.allow_user_override
                if profile.context_defaults
                else []
            )
            applied = {}
            for key, value in user_overrides.items():
                if not allowed or key in allowed:
                    applied[key] = value
                else:
                    logger.warning(f"User override for '{key}' not allowed; ignored")
            context.update(applied)
            logger.debug(f"Applied {len(applied)} user overrides (allowlisted)")
        
        return context
    
    def _extract_regex(
        self,
        patterns: list[RegexPattern],
        file_path: Path,
    ) -> dict[str, Any]:
        """Extract values using regex patterns.
        
        Args:
            patterns: List of regex patterns from profile
            file_path: File path to extract from
            
        Returns:
            Dictionary of extracted values
        """
        results: dict[str, Any] = {}
        
        for pattern in patterns:
            scope_value = self._get_scope_value(pattern.scope, file_path)
            
            try:
                match = re.search(pattern.pattern, scope_value)
                if match:
                    groups = match.groupdict()
                    if pattern.field in groups:
                        value = groups[pattern.field]
                        # Apply transform if specified (per DESIGN §4)
                        if pattern.transform:
                            value = self._apply_transform(
                                value,
                                pattern.transform,
                                pattern.transform_args,
                            )
                        results[pattern.field] = value
                elif pattern.required:
                    if pattern.on_fail == "error":
                        raise ValueError(
                            f"Required pattern '{pattern.field}' not matched in {scope_value}"
                        )
                    else:
                        logger.warning(
                            f"Required pattern '{pattern.field}' not matched in {scope_value}"
                        )
            except re.error as e:
                logger.error(f"Invalid regex for {pattern.field}: {e}")
        
        return results
    
    def _extract_content_patterns(
        self,
        patterns: list[ContentPattern],
        content: dict,
    ) -> dict[str, Any]:
        """Extract values using JSONPath content patterns."""
        results: dict[str, Any] = {}
        for pattern in patterns:
            try:
                value = self._get_jsonpath_value(content, pattern.path)
                if value is not None:
                    results[pattern.field] = value
                elif pattern.default is not None:
                    results[pattern.field] = pattern.default
                elif pattern.required:
                    if pattern.on_fail == "error":
                        raise ValueError(f"Required JSONPath '{pattern.field}' not found")
                    elif pattern.on_fail == "skip_file":
                        logger.warning(
                            f"Required JSONPath '{pattern.field}' not found; configured skip_file"
                        )
                    else:
                        logger.warning(f"Required JSONPath '{pattern.field}' not found")
            except Exception as e:
                logger.error(f"JSONPath error for {pattern.field}: {e}")
        return results
    
    def _get_scope_value(self, scope: str, file_path: Path) -> str:
        """Get string value based on scope.
        
        Args:
            scope: Scope type ('filename', 'path', 'full_path')
            file_path: File path
            
        Returns:
            String to match against
        """
        if scope == "filename":
            return file_path.name
        elif scope == "path":
            return str(file_path.parent)
        elif scope == "full_path":
            return str(file_path)
        else:
            return file_path.name
    
    def _get_jsonpath_value(self, data: dict, path: str) -> Any:
        """Get value at JSONPath.
        
        Args:
            data: Dictionary to search
            path: JSONPath expression
            
        Returns:
            Value at path or None
        """
        if not path.startswith("$"):
            path = f"$.{path}"
        
        try:
            expr = jsonpath_parse(path)
            matches = expr.find(data)
            if matches:
                return matches[0].value
        except Exception:
            pass
        
        return None
    
    def _apply_transform(
        self,
        value: str,
        transform: str,
        args: dict | None = None,
    ) -> Any:
        """Apply transform to extracted value.
        
        Args:
            value: Raw extracted value
            transform: Transform name
            args: Transform arguments
            
        Returns:
            Transformed value
        """
        args = args or {}
        
        if transform == "parse_date":
            fmt = args.get("format", "%Y%m%d")
            try:
                return datetime.strptime(value, fmt)
            except ValueError:
                return value
        elif transform == "uppercase":
            return value.upper()
        elif transform == "lowercase":
            return value.lower()
        elif transform == "strip":
            return value.strip()
        else:
            return value


def extract_context(
    profile: DATProfile,
    file_path: Path,
    file_content: dict | None = None,
    user_overrides: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Convenience function for context extraction.
    
    Args:
        profile: DATProfile with context configuration
        file_path: Path to file
        file_content: Parsed file content
        user_overrides: User-provided overrides
        
    Returns:
        Merged context dictionary
    """
    extractor = ContextExtractor()
    return extractor.extract(profile, file_path, file_content, user_overrides)
