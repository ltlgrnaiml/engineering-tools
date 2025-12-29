"""ValidationEngine - Stable columns and schema validation.

Per ADR-0011: Stable column policies enforce schema expectations.
Validates extracted DataFrames against profile-defined rules.
"""

import logging
from dataclasses import dataclass, field
from typing import Any

import polars as pl

from .profile_loader import DATProfile, TableConfig

logger = logging.getLogger(__name__)


@dataclass
class ValidationResult:
    """Result of table validation."""
    table_id: str
    valid: bool
    errors: list[str] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    missing_columns: list[str] = field(default_factory=list)
    extra_columns: list[str] = field(default_factory=list)


@dataclass
class ProfileValidationSummary:
    """Summary of all table validations."""
    profile_id: str
    valid: bool
    total_tables: int
    valid_tables: int
    table_results: list[ValidationResult] = field(default_factory=list)
    
    @property
    def error_count(self) -> int:
        return sum(len(r.errors) for r in self.table_results)
    
    @property
    def warning_count(self) -> int:
        return sum(len(r.warnings) for r in self.table_results)


class ValidationEngine:
    """Validates extracted DataFrames against profile rules.
    
    Per ADR-0011: Enforces stable column policies and schema constraints.
    """
    
    def validate_table(
        self,
        df: pl.DataFrame,
        table_config: TableConfig,
    ) -> ValidationResult:
        """Validate DataFrame against table configuration.
        
        Args:
            df: DataFrame to validate
            table_config: Table configuration with stable_columns
            
        Returns:
            ValidationResult with errors/warnings
        """
        errors: list[str] = []
        warnings: list[str] = []
        missing: list[str] = []
        extra: list[str] = []
        
        if not table_config.stable_columns:
            return ValidationResult(
                table_id=table_config.id,
                valid=True,
            )
        
        actual_cols = set(df.columns)
        expected_cols = set(table_config.stable_columns)
        
        # Check for missing columns
        missing = list(expected_cols - actual_cols)
        
        # Check for extra columns (if not subset mode)
        if not table_config.stable_columns_subset:
            extra = list(actual_cols - expected_cols)
        
        # Apply mode
        mode = table_config.stable_columns_mode
        
        if missing:
            msg = f"Missing stable columns: {missing}"
            if mode == "error":
                errors.append(msg)
            elif mode == "warn":
                warnings.append(msg)
        
        if extra and not table_config.stable_columns_subset:
            msg = f"Unexpected columns: {extra}"
            if mode == "error":
                errors.append(msg)
            elif mode == "warn":
                warnings.append(msg)
        
        # Per DESIGN §7: Validate value constraints if defined
        if table_config.validation_constraints:
            constraint_errors = self.validate_value_constraints(
                df, table_config.validation_constraints
            )
            for err in constraint_errors:
                if mode == "error":
                    errors.append(err)
                elif mode == "warn":
                    warnings.append(err)
        
        return ValidationResult(
            table_id=table_config.id,
            valid=len(errors) == 0,
            errors=errors,
            warnings=warnings,
            missing_columns=missing,
            extra_columns=extra,
        )
    
    def validate_extraction(
        self,
        results: dict[str, pl.DataFrame],
        profile: DATProfile,
    ) -> ProfileValidationSummary:
        """Validate all extracted tables against profile.
        
        Args:
            results: Dict of table_id to DataFrame
            profile: DATProfile with validation rules
            
        Returns:
            ProfileValidationSummary with all results
        """
        table_results: list[ValidationResult] = []
        
        for level_name, table_config in profile.get_all_tables():
            if table_config.id not in results:
                # Table not extracted - check if required
                table_results.append(ValidationResult(
                    table_id=table_config.id,
                    valid=True,  # Not extracted is OK
                    warnings=[f"Table {table_config.id} not extracted"],
                ))
                continue
            
            df = results[table_config.id]
            result = self.validate_table(df, table_config)
            table_results.append(result)
            
            # Log warnings
            for warning in result.warnings:
                logger.warning(f"[{table_config.id}] {warning}")
            for error in result.errors:
                logger.error(f"[{table_config.id}] {error}")
        
        # Per DESIGN §7: Apply profile-level validation rules
        profile_errors: list[str] = []
        profile_warnings: list[str] = []
        
        # Schema rules validation
        if profile.schema_rules:
            for table_id, df in results.items():
                schema_errors = self.validate_schema_rules(df, profile.schema_rules)
                profile_errors.extend(schema_errors)
        
        # Row rules validation
        if profile.row_rules:
            for table_id, df in results.items():
                row_errors = self.validate_row_rules(df, profile.row_rules)
                for err in row_errors:
                    if err.startswith("ERROR:"):
                        profile_errors.append(err)
                    else:
                        profile_warnings.append(err)
        
        # Aggregate rules validation
        if profile.aggregate_rules:
            for table_id, df in results.items():
                agg_errors = self.validate_aggregate_rules(df, profile.aggregate_rules)
                for err in agg_errors:
                    if err.startswith("ERROR:"):
                        profile_errors.append(err)
                    else:
                        profile_warnings.append(err)
        
        # Log profile-level validation results
        for err in profile_errors:
            logger.error(f"[PROFILE] {err}")
        for warn in profile_warnings:
            logger.warning(f"[PROFILE] {warn}")
        
        all_valid = all(r.valid for r in table_results) and len(profile_errors) == 0
        
        return ProfileValidationSummary(
            profile_id=profile.profile_id,
            valid=all_valid,
            total_tables=len(table_results),
            valid_tables=sum(1 for r in table_results if r.valid),
            table_results=table_results,
        )
    
    def validate_value_constraints(
        self,
        df: pl.DataFrame,
        constraints: list[dict[str, Any]],
    ) -> list[str]:
        """Validate value constraints on DataFrame.
        
        Args:
            df: DataFrame to validate
            constraints: List of constraint definitions
            
        Returns:
            List of validation error messages
        """
        errors: list[str] = []
        
        for constraint in constraints:
            col = constraint.get("column")
            if not col or col not in df.columns:
                continue
            
            constraint_type = constraint.get("type")
            
            if constraint_type == "range":
                min_val = constraint.get("min")
                max_val = constraint.get("max")
                
                if min_val is not None:
                    violations = df.filter(pl.col(col) < min_val)
                    if len(violations) > 0:
                        errors.append(
                            f"Column {col} has {len(violations)} values below {min_val}"
                        )
                
                if max_val is not None:
                    violations = df.filter(pl.col(col) > max_val)
                    if len(violations) > 0:
                        errors.append(
                            f"Column {col} has {len(violations)} values above {max_val}"
                        )
            
            elif constraint_type == "not_null":
                null_count = df.filter(pl.col(col).is_null()).height
                if null_count > 0:
                    errors.append(f"Column {col} has {null_count} null values")
            
            elif constraint_type == "regex":
                pattern = constraint.get("pattern")
                if pattern:
                    try:
                        # Check string column matches pattern
                        non_matches = df.filter(
                            ~pl.col(col).cast(pl.Utf8).str.contains(pattern)
                        )
                        if len(non_matches) > 0:
                            errors.append(
                                f"Column {col} has {len(non_matches)} values "
                                f"not matching pattern {pattern}"
                            )
                    except Exception as e:
                        errors.append(f"Regex validation error for {col}: {e}")
        
        return errors
    
    def validate_schema_rules(
        self,
        df: pl.DataFrame,
        schema_rules: dict[str, Any],
    ) -> list[str]:
        """Validate schema rules per DESIGN §7.
        
        Args:
            df: DataFrame to validate
            schema_rules: Dict with required_columns, column_types, unique_columns
            
        Returns:
            List of validation error messages
        """
        errors: list[str] = []
        
        # Check required columns
        required_cols = schema_rules.get("required_columns", [])
        for col in required_cols:
            if col not in df.columns:
                errors.append(f"Required column missing: {col}")
        
        # Check column types
        column_types = schema_rules.get("column_types", {})
        for col, expected_type in column_types.items():
            if col not in df.columns:
                continue
            
            actual_type = str(df[col].dtype).lower()
            expected_lower = expected_type.lower()
            
            # Map common type names
            type_matches = {
                "string": ["utf8", "str", "string", "object"],
                "float": ["float64", "float32", "float", "f64", "f32"],
                "int": ["int64", "int32", "int16", "int8", "i64", "i32"],
                "bool": ["bool", "boolean"],
                "datetime": ["datetime", "date"],
            }
            
            valid_types = type_matches.get(expected_lower, [expected_lower])
            if not any(t in actual_type for t in valid_types):
                errors.append(
                    f"Column {col} type mismatch: expected {expected_type}, "
                    f"got {actual_type}"
                )
        
        # Check unique columns
        unique_cols = schema_rules.get("unique_columns", [])
        for col in unique_cols:
            if col not in df.columns:
                continue
            
            total = len(df)
            unique = df[col].n_unique()
            if unique < total:
                errors.append(
                    f"Column {col} has {total - unique} duplicate values"
                )
        
        return errors
    
    def validate_row_rules(
        self,
        df: pl.DataFrame,
        row_rules: list[dict[str, Any]],
    ) -> list[str]:
        """Validate row-level rules per DESIGN §7.
        
        Args:
            df: DataFrame to validate
            row_rules: List of rule definitions with name, expression, on_fail
            
        Returns:
            List of validation error/warning messages
        """
        errors: list[str] = []
        
        for rule in row_rules:
            name = rule.get("name", "unnamed")
            expression = rule.get("expression", "")
            on_fail = rule.get("on_fail", "warn")
            message = rule.get("message", f"Row rule '{name}' failed")
            
            if not expression:
                continue
            
            try:
                # Parse simple boolean expressions
                # Format: "col1 > 0 AND col2 > 0"
                violations = self._evaluate_row_expression(df, expression)
                if violations > 0:
                    msg = f"{message} ({violations} rows)"
                    if on_fail == "error":
                        errors.append(f"ERROR: {msg}")
                    else:
                        errors.append(f"WARN: {msg}")
            except Exception as e:
                errors.append(f"Row rule evaluation error for '{name}': {e}")
        
        return errors
    
    def _evaluate_row_expression(
        self,
        df: pl.DataFrame,
        expression: str,
    ) -> int:
        """Evaluate a row expression and return count of violations.
        
        Supports simple expressions like "col > 0 AND col2 > 0"
        """
        # Split on AND/OR
        parts = expression.upper().split(" AND ")
        
        filter_expr = None
        for part in parts:
            part = part.strip()
            
            # Parse comparison: "col > value"
            for op in [" >= ", " <= ", " > ", " < ", " == ", " != "]:
                if op in part.upper():
                    col, val = part.split(op.strip(), 1)
                    col = col.strip()
                    val = val.strip()
                    
                    if col not in df.columns:
                        continue
                    
                    try:
                        val_num = float(val)
                        if ">=" in op:
                            cond = pl.col(col) >= val_num
                        elif "<=" in op:
                            cond = pl.col(col) <= val_num
                        elif ">" in op:
                            cond = pl.col(col) > val_num
                        elif "<" in op:
                            cond = pl.col(col) < val_num
                        elif "==" in op:
                            cond = pl.col(col) == val_num
                        elif "!=" in op:
                            cond = pl.col(col) != val_num
                        else:
                            continue
                        
                        if filter_expr is None:
                            filter_expr = cond
                        else:
                            filter_expr = filter_expr & cond
                    except ValueError:
                        continue
                    break
        
        if filter_expr is None:
            return 0
        
        # Count rows that DON'T match (violations)
        passing = df.filter(filter_expr).height
        return len(df) - passing
    
    def validate_aggregate_rules(
        self,
        df: pl.DataFrame,
        aggregate_rules: list[dict[str, Any]],
    ) -> list[str]:
        """Validate aggregate rules per DESIGN §7.
        
        Args:
            df: DataFrame to validate
            aggregate_rules: List of rule definitions
            
        Returns:
            List of validation error/warning messages
        """
        errors: list[str] = []
        
        for rule in aggregate_rules:
            name = rule.get("name", "unnamed")
            rule_type = rule.get("type", "")
            on_fail = rule.get("on_fail", "warn")
            message = rule.get("message", f"Aggregate rule '{name}' failed")
            
            try:
                if rule_type == "row_count":
                    min_count = rule.get("min", 0)
                    max_count = rule.get("max", float("inf"))
                    actual = len(df)
                    
                    if actual < min_count:
                        msg = f"{message}: row count {actual} < min {min_count}"
                        errors.append(f"{'ERROR' if on_fail == 'error' else 'WARN'}: {msg}")
                    elif actual > max_count:
                        msg = f"{message}: row count {actual} > max {max_count}"
                        errors.append(f"{'ERROR' if on_fail == 'error' else 'WARN'}: {msg}")
                
                elif rule_type == "unique_count":
                    col = rule.get("column")
                    min_count = rule.get("min", 0)
                    
                    if col and col in df.columns:
                        actual = df[col].n_unique()
                        if actual < min_count:
                            msg = f"{message}: unique count {actual} < min {min_count}"
                            errors.append(f"{'ERROR' if on_fail == 'error' else 'WARN'}: {msg}")
                
                elif rule_type == "null_ratio":
                    col = rule.get("column")
                    max_ratio = rule.get("max", 1.0)
                    
                    if col and col in df.columns:
                        null_count = df.filter(pl.col(col).is_null()).height
                        ratio = null_count / len(df) if len(df) > 0 else 0
                        if ratio > max_ratio:
                            msg = f"{message}: null ratio {ratio:.2%} > max {max_ratio:.2%}"
                            errors.append(f"{'ERROR' if on_fail == 'error' else 'WARN'}: {msg}")
                            
            except Exception as e:
                errors.append(f"Aggregate rule error for '{name}': {e}")
        
        return errors


def validate_extraction(
    results: dict[str, pl.DataFrame],
    profile: DATProfile,
) -> ProfileValidationSummary:
    """Convenience function for extraction validation.
    
    Args:
        results: Dict of table_id to DataFrame
        profile: DATProfile with validation rules
        
    Returns:
        ProfileValidationSummary
    """
    engine = ValidationEngine()
    return engine.validate_extraction(results, profile)
