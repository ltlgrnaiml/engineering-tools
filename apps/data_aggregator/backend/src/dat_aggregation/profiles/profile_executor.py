"""ProfileExecutor - Core engine for profile-driven extraction.

Per ADR-0011: All data extraction is governed by versioned profiles.
The ProfileExecutor interprets profiles and produces flat, tabular DataFrames.
"""

import json
import logging
from pathlib import Path
from typing import Any

import polars as pl

from .profile_loader import DATProfile, TableConfig, TableSelect
from .strategies import get_strategy
from .strategies.base import SelectConfig, RepeatOverConfig
from .file_filter import filter_files
from .transform_pipeline import TransformPipeline, ColumnTransform

logger = logging.getLogger(__name__)


class ProfileExecutor:
    """Interprets profiles and executes extraction per ADR-0011.
    
    The ProfileExecutor is the core engine that:
    1. Loads file content via adapters
    2. Executes extraction strategies defined in profile
    3. Applies context columns to extracted data
    4. Returns Dict[table_id, DataFrame]
    """
    
    def __init__(self, jsonpath_engine: str = "jsonpath-ng"):
        """Initialize ProfileExecutor.
        
        Args:
            jsonpath_engine: JSONPath engine to use ('jsonpath-ng' or 'jmespath')
        """
        self.jsonpath_engine = jsonpath_engine
    
    def _check_governance_limits(
        self,
        profile: DATProfile,
        files: list[Path],
    ) -> list[str]:
        """Check governance limits before extraction per DESIGN §10.
        
        Args:
            profile: DATProfile with governance config
            files: List of files to process
            
        Returns:
            List of limit violation messages (empty if all OK)
        """
        violations: list[str] = []
        
        if not profile.governance or not profile.governance.limits:
            return violations
        
        limits = profile.governance.limits
        
        # Check file count limit
        if len(files) > limits.max_files_per_run:
            violations.append(
                f"File count {len(files)} exceeds limit {limits.max_files_per_run}"
            )
        
        # Check individual file size limits
        for file_path in files:
            try:
                file_size_mb = file_path.stat().st_size / (1024 * 1024)
                if file_size_mb > limits.max_file_size_mb:
                    violations.append(
                        f"File {file_path.name} ({file_size_mb:.1f}MB) exceeds "
                        f"limit {limits.max_file_size_mb}MB"
                    )
            except OSError:
                pass
        
        # Check total size limit
        total_size_gb = sum(
            f.stat().st_size for f in files if f.exists()
        ) / (1024 * 1024 * 1024)
        if total_size_gb > limits.max_total_size_gb:
            violations.append(
                f"Total size {total_size_gb:.2f}GB exceeds limit {limits.max_total_size_gb}GB"
            )
        
        # Check table count limit
        table_count = len(profile.get_all_tables())
        max_tables = limits.max_tables_per_level * len(profile.levels)
        if table_count > max_tables:
            violations.append(
                f"Table count {table_count} exceeds limit {max_tables}"
            )
        
        return violations
    
    def _check_access_control(
        self,
        profile: DATProfile,
        action: str,
        user_roles: list[str] | None = None,
    ) -> str | None:
        """Check access control per DESIGN §10.
        
        Args:
            profile: DATProfile with governance config
            action: Action to check ('read', 'modify', 'delete')
            user_roles: User's roles (defaults to ['all'] if None)
            
        Returns:
            Error message if access denied, None if allowed
        """
        if not profile.governance or not profile.governance.access:
            return None  # No access control configured = allow all
        
        access = profile.governance.access
        user_roles = user_roles or ["all"]
        
        # Get allowed roles for this action
        if action == "read":
            allowed_roles = access.read
        elif action == "modify":
            allowed_roles = access.modify
        elif action == "delete":
            allowed_roles = access.delete
        else:
            return f"Unknown action: {action}"
        
        # Check if user has any allowed role
        if "all" in allowed_roles:
            return None  # Anyone can access
        
        if any(role in allowed_roles for role in user_roles):
            return None  # User has required role
        
        return f"Action '{action}' requires one of {allowed_roles}, user has {user_roles}"
    
    async def execute(
        self,
        profile: DATProfile,
        files: list[Path],
        context: dict[str, Any],
        selected_tables: list[str] | None = None,
    ) -> dict[str, pl.DataFrame]:
        """Execute full profile extraction.
        
        Args:
            profile: Loaded DATProfile
            files: List of files to process
            context: Context dictionary (from context stage)
            selected_tables: Optional filter for specific tables
            
        Returns:
            Dict mapping table_id to extracted DataFrame
            
        Raises:
            ValueError: If governance limits are exceeded
        """
        # Per DESIGN §10: Check governance limits before extraction
        limit_violations = self._check_governance_limits(profile, files)
        if limit_violations:
            for violation in limit_violations:
                logger.error(f"Governance limit violation: {violation}")
            raise ValueError(f"Governance limits exceeded: {limit_violations}")
        
        # Per DESIGN §10: Check access control
        access_denied = self._check_access_control(profile, "read")
        if access_denied:
            logger.error(f"Access denied: {access_denied}")
            raise PermissionError(f"Access denied: {access_denied}")
        
        # Per DESIGN §10: Audit logging for extraction start
        if profile.governance and profile.governance.audit:
            if profile.governance.audit.log_access:
                logger.info(
                    f"AUDIT: Profile extraction started - "
                    f"profile_id={profile.profile_id}, files={len(files)}"
                )
        
        results: dict[str, pl.DataFrame] = {}
        
        # Per DESIGN §2: Apply file filter predicates if defined
        filtered_files = filter_files(files, profile.datasource_filters)
        if len(filtered_files) < len(files):
            logger.info(
                f"File filter applied: {len(files)} -> {len(filtered_files)} files"
            )
        
        for file_path in filtered_files:
            # Load file content
            data = await self._load_file(file_path, profile)
            if data is None:
                logger.warning(f"Could not load file: {file_path}")
                continue
            
            # Extract each table
            for level_name, table_config in profile.get_all_tables():
                if selected_tables and table_config.id not in selected_tables:
                    continue
                
                try:
                    df = self.extract_table(table_config, data, context)
                    
                    if df.is_empty():
                        continue
                    
                    # Per DESIGN §6: Apply table-level column_transforms if defined
                    if table_config.column_transforms:
                        pipeline = TransformPipeline()
                        transforms = [
                            ColumnTransform(
                                source=t.get("source", ""),
                                target=t.get("target", t.get("source", "")),
                                transform=t.get("transform", ""),
                                args=t.get("args"),
                            )
                            for t in table_config.column_transforms
                        ]
                        df = pipeline.apply_column_transforms(df, transforms)
                    
                    # Apply context columns for this level
                    df = self._apply_context(df, context, level_name, profile)
                    
                    # Accumulate results
                    if table_config.id in results:
                        results[table_config.id] = pl.concat([
                            results[table_config.id], df
                        ], how="diagonal")
                    else:
                        results[table_config.id] = df
                        
                except Exception as e:
                    logger.error(f"Error extracting table {table_config.id}: {e}")
                    continue
        
        # Per DESIGN §10: Audit logging for extraction completion
        if profile.governance and profile.governance.audit:
            if profile.governance.audit.log_access:
                total_rows = sum(len(df) for df in results.values())
                logger.info(
                    f"AUDIT: Profile extraction completed - "
                    f"profile_id={profile.profile_id}, "
                    f"tables={len(results)}, rows={total_rows}"
                )
        
        return results
    
    def extract_table(
        self,
        table_config: TableConfig,
        data: Any,
        context: dict[str, Any],
    ) -> pl.DataFrame:
        """Extract single table using configured strategy.
        
        Args:
            table_config: Table configuration from profile
            data: Loaded file data (parsed JSON)
            context: Context dictionary
            
        Returns:
            Extracted DataFrame
        """
        if not table_config.select:
            logger.warning(f"No select config for table {table_config.id}")
            return pl.DataFrame()
        
        # Build SelectConfig from profile TableSelect
        select_config = self._build_select_config(table_config.select)
        
        # Get strategy
        strategy_name = select_config.strategy
        
        # Handle repeat_over - it wraps the base strategy
        if select_config.repeat_over:
            strategy_name = "repeat_over"
        
        try:
            strategy = get_strategy(strategy_name)
        except ValueError as e:
            logger.error(f"Strategy error for {table_config.id}: {e}")
            return pl.DataFrame()
        
        # Execute extraction
        return strategy.extract(data, select_config, context)
    
    def _build_select_config(self, table_select: TableSelect) -> SelectConfig:
        """Build SelectConfig from profile TableSelect."""
        repeat_over = None
        if table_select.repeat_over:
            repeat_over = RepeatOverConfig(
                path=table_select.repeat_over.get("path", ""),
                as_var=table_select.repeat_over.get("as", ""),
                inject_fields=table_select.repeat_over.get("inject_fields", {}),
            )
        
        return SelectConfig(
            strategy=table_select.strategy,
            path=table_select.path,
            headers_key=table_select.headers_key,
            data_key=table_select.data_key,
            repeat_over=repeat_over,
        )
    
    def _apply_context(
        self,
        df: pl.DataFrame,
        context: dict[str, Any],
        level_name: str,
        profile: DATProfile,
    ) -> pl.DataFrame:
        """Apply context columns to DataFrame.
        
        Args:
            df: DataFrame to augment
            context: Context dictionary
            level_name: Level name (run, image, etc.)
            profile: Profile for context config lookup
            
        Returns:
            DataFrame with context columns added
        """
        # Find context config for this level
        context_config = None
        for ctx in profile.contexts:
            if ctx.level == level_name:
                context_config = ctx
                break
        
        if not context_config:
            # No specific context config, add all context as columns
            for key, value in context.items():
                if key not in df.columns:
                    df = df.with_columns(pl.lit(value).alias(key))
            return df
        
        # Apply key_map if defined
        for target_col, source_path in context_config.key_map.items():
            if target_col not in df.columns:
                value = context.get(target_col) or context.get(source_path.lstrip("$."))
                if value is not None:
                    df = df.with_columns(pl.lit(value).alias(target_col))
        
        return df
    
    async def _load_file(
        self,
        file_path: Path,
        profile: DATProfile,
    ) -> Any:
        """Load file content based on profile format.
        
        Per DESIGN §2: Supports JSON, CSV, Excel, Parquet formats.
        
        Args:
            file_path: Path to file
            profile: Profile with format info
            
        Returns:
            Parsed file content (dict for JSON, DataFrame for tabular)
        """
        fmt = profile.datasource_format.lower()
        
        if fmt == "json":
            return self._load_json(file_path)
        elif fmt == "csv":
            return self._load_csv(file_path, profile.datasource_options)
        elif fmt == "excel":
            return self._load_excel(file_path, profile.datasource_options)
        elif fmt == "parquet":
            return self._load_parquet(file_path)
        else:
            # Try to infer from extension
            ext = file_path.suffix.lower()
            if ext == ".json":
                return self._load_json(file_path)
            elif ext == ".csv":
                return self._load_csv(file_path, profile.datasource_options)
            elif ext in (".xlsx", ".xls"):
                return self._load_excel(file_path, profile.datasource_options)
            elif ext == ".parquet":
                return self._load_parquet(file_path)
            else:
                logger.warning(f"Unknown format '{fmt}', attempting JSON")
                return self._load_json(file_path)
    
    def _load_json(self, file_path: Path) -> dict | None:
        """Load JSON file."""
        try:
            with open(file_path, encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError) as e:
            logger.error(f"Error loading JSON {file_path}: {e}")
            return None
    
    def _load_csv(
        self, file_path: Path, options: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Load CSV file as dict with 'data' key containing records.
        
        Per DESIGN §2: Supports CSV format options.
        """
        try:
            csv_opts = options.get("csv", {})
            delimiter = csv_opts.get("delimiter", ",")
            encoding = csv_opts.get("encoding", "utf-8")
            skip_rows = csv_opts.get("skip_rows", 0)
            
            df = pl.read_csv(
                file_path,
                separator=delimiter,
                encoding=encoding,
                skip_rows=skip_rows,
            )
            # Return as dict with records for strategy compatibility
            return {"data": df.to_dicts(), "_dataframe": df}
        except Exception as e:
            logger.error(f"Error loading CSV {file_path}: {e}")
            return None
    
    def _load_excel(
        self, file_path: Path, options: dict[str, Any]
    ) -> dict[str, Any] | None:
        """Load Excel file as dict with sheet data.
        
        Per DESIGN §2: Supports Excel format options.
        """
        try:
            excel_opts = options.get("excel", {})
            sheet_selection = excel_opts.get("sheet_selection", "first")
            
            if sheet_selection == "all":
                # Load all sheets
                sheets_data = {}
                df_dict = pl.read_excel(file_path, sheet_id=0)
                # For now, load first sheet - full multi-sheet support later
                sheets_data["Sheet1"] = df_dict.to_dicts()
                return {"sheets": sheets_data, "_dataframe": df_dict}
            else:
                # Load first or specific sheet
                df = pl.read_excel(file_path)
                return {"data": df.to_dicts(), "_dataframe": df}
        except Exception as e:
            logger.error(f"Error loading Excel {file_path}: {e}")
            return None
    
    def _load_parquet(self, file_path: Path) -> dict[str, Any] | None:
        """Load Parquet file as dict with records."""
        try:
            df = pl.read_parquet(file_path)
            return {"data": df.to_dicts(), "_dataframe": df}
        except Exception as e:
            logger.error(f"Error loading Parquet {file_path}: {e}")
            return None


async def execute_profile_extraction(
    profile: DATProfile,
    files: list[Path],
    context: dict[str, Any],
    selected_tables: list[str] | None = None,
) -> dict[str, pl.DataFrame]:
    """Convenience function for profile extraction.
    
    Args:
        profile: Loaded DATProfile
        files: Files to process
        context: Context dictionary
        selected_tables: Optional table filter
        
    Returns:
        Dict mapping table_id to DataFrame
    """
    executor = ProfileExecutor()
    return await executor.execute(profile, files, context, selected_tables)
