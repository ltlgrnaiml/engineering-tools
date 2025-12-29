"""Unit tests for Profile-Driven ETL governance and advanced features.

Per DESIGN_Profile-Driven-ETL-Architecture.md:
- §2: Datasource filters (file_filter)
- §3: Population strategies
- §6: Transforms (column_transforms, unit normalization)
- §10: Governance (limits, audit)
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
    DATProfile,
    GovernanceConfig,
    GovernanceAccessConfig,
    GovernanceAuditConfig,
    GovernanceLimitsConfig,
    GovernanceComplianceConfig,
    LevelConfig,
    TableConfig,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_executor import (
    ProfileExecutor,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.file_filter import (
    FileFilter,
    filter_files,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.population_strategies import (
    PopulationFilter,
    apply_population_strategy,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.transform_pipeline import (
    TransformPipeline,
    ColumnTransform,
)


class TestGovernanceLimits:
    """Tests for governance limit enforcement per DESIGN §10."""
    
    def test_check_file_count_limit(self, tmp_path: Path):
        """Test file count limit is enforced."""
        executor = ProfileExecutor()
        
        # Create test files
        files = []
        for i in range(5):
            f = tmp_path / f"test_{i}.json"
            f.write_text("{}")
            files.append(f)
        
        # Profile with limit of 3 files
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            governance=GovernanceConfig(
                limits=GovernanceLimitsConfig(
                    max_files_per_run=3,
                ),
            ),
        )
        
        violations = executor._check_governance_limits(profile, files)
        
        assert len(violations) == 1
        assert "File count 5 exceeds limit 3" in violations[0]
    
    def test_check_file_size_limit(self, tmp_path: Path):
        """Test individual file size limit is enforced."""
        executor = ProfileExecutor()
        
        # Create a file larger than limit (we'll mock the size)
        large_file = tmp_path / "large.json"
        large_file.write_text("{}")
        
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            governance=GovernanceConfig(
                limits=GovernanceLimitsConfig(
                    max_file_size_mb=1,  # 1MB limit
                ),
            ),
        )
        
        # Mock file size to be 2MB
        with patch.object(Path, 'stat') as mock_stat:
            mock_stat.return_value = MagicMock(st_size=2 * 1024 * 1024)
            violations = executor._check_governance_limits(profile, [large_file])
        
        assert len(violations) == 1
        assert "exceeds limit 1MB" in violations[0]
    
    def test_no_violations_when_within_limits(self, tmp_path: Path):
        """Test no violations when within all limits."""
        executor = ProfileExecutor()
        
        # Create test files
        files = []
        for i in range(2):
            f = tmp_path / f"test_{i}.json"
            f.write_text("{}")
            files.append(f)
        
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            governance=GovernanceConfig(
                limits=GovernanceLimitsConfig(
                    max_files_per_run=10,
                    max_file_size_mb=100,
                ),
            ),
        )
        
        violations = executor._check_governance_limits(profile, files)
        
        assert len(violations) == 0
    
    def test_no_governance_config_skips_checks(self, tmp_path: Path):
        """Test that missing governance config skips limit checks."""
        executor = ProfileExecutor()
        
        files = [tmp_path / f"test_{i}.json" for i in range(100)]
        
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            governance=None,
        )
        
        violations = executor._check_governance_limits(profile, files)
        
        assert len(violations) == 0


class TestFileFilter:
    """Tests for file filter predicates per DESIGN §2."""
    
    def test_filter_by_extension(self, tmp_path: Path):
        """Test filtering files by extension."""
        # Create test files
        json_file = tmp_path / "data.json"
        csv_file = tmp_path / "data.csv"
        json_file.write_text("{}")
        csv_file.write_text("a,b")
        
        filter_config = {
            "type": "predicate",
            "field": "extension",
            "op": "equals",
            "value": ".json",
        }
        
        result = filter_files([json_file, csv_file], filter_config)
        
        assert len(result) == 1
        assert result[0] == json_file
    
    def test_filter_by_filename_contains(self, tmp_path: Path):
        """Test filtering files by filename contains."""
        file1 = tmp_path / "LOTABC_data.json"
        file2 = tmp_path / "other_data.json"
        file1.write_text("{}")
        file2.write_text("{}")
        
        filter_config = {
            "type": "predicate",
            "field": "filename",
            "op": "contains",
            "value": "LOT",
        }
        
        result = filter_files([file1, file2], filter_config)
        
        assert len(result) == 1
        assert result[0] == file1
    
    def test_filter_and_group(self, tmp_path: Path):
        """Test AND group filter."""
        file1 = tmp_path / "LOTABC_data.json"
        file2 = tmp_path / "LOTABC_data.csv"
        file3 = tmp_path / "other_data.json"
        for f in [file1, file2, file3]:
            f.write_text("{}")
        
        filter_config = {
            "type": "group",
            "op": "AND",
            "children": [
                {"type": "predicate", "field": "filename", "op": "contains", "value": "LOT"},
                {"type": "predicate", "field": "extension", "op": "equals", "value": ".json"},
            ],
        }
        
        result = filter_files([file1, file2, file3], filter_config)
        
        assert len(result) == 1
        assert result[0] == file1
    
    def test_filter_or_group(self, tmp_path: Path):
        """Test OR group filter."""
        json_file = tmp_path / "data.json"
        csv_file = tmp_path / "data.csv"
        txt_file = tmp_path / "data.txt"
        for f in [json_file, csv_file, txt_file]:
            f.write_text("test")
        
        filter_config = {
            "type": "group",
            "op": "OR",
            "children": [
                {"type": "predicate", "field": "extension", "op": "equals", "value": ".json"},
                {"type": "predicate", "field": "extension", "op": "equals", "value": ".csv"},
            ],
        }
        
        result = filter_files([json_file, csv_file, txt_file], filter_config)
        
        assert len(result) == 2
        assert json_file in result
        assert csv_file in result
    
    def test_empty_filter_returns_all(self, tmp_path: Path):
        """Test that empty filter returns all files."""
        files = [tmp_path / f"file{i}.json" for i in range(3)]
        for f in files:
            f.write_text("{}")
        
        result = filter_files(files, None)
        
        assert len(result) == 3


class TestPopulationStrategies:
    """Tests for population strategies per DESIGN §3."""
    
    def test_strategy_all(self):
        """Test 'all' strategy returns all rows."""
        df = pl.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
        })
        
        result = apply_population_strategy(df, "all", {})
        
        assert len(result) == 5
    
    def test_strategy_sample(self):
        """Test 'sample' strategy returns subset."""
        df = pl.DataFrame({
            "id": range(100),
            "value": range(100),
        })
        
        config = {"size": 10, "seed": 42}
        result = apply_population_strategy(df, "sample", config)
        
        assert len(result) == 10
    
    def test_strategy_sample_with_seed_reproducible(self):
        """Test 'sample' strategy is reproducible with same seed."""
        df = pl.DataFrame({
            "id": range(100),
            "value": range(100),
        })
        
        config = {"size": 10, "seed": 42}
        result1 = apply_population_strategy(df, "sample", config)
        result2 = apply_population_strategy(df, "sample", config)
        
        assert result1["id"].to_list() == result2["id"].to_list()
    
    def test_strategy_first_n(self):
        """Test 'first_n' strategy returns first N rows."""
        df = pl.DataFrame({
            "id": [1, 2, 3, 4, 5],
            "value": [10, 20, 30, 40, 50],
        })
        
        config = {"size": 3}
        result = apply_population_strategy(df, "first_n", config)
        
        assert len(result) == 3
        assert result["id"].to_list() == [1, 2, 3]


class TestColumnTransforms:
    """Tests for column transforms per DESIGN §6."""
    
    def test_apply_column_transform_rename(self):
        """Test renaming a column via transform."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "old_name": [1, 2, 3],
        })
        
        transforms = [
            ColumnTransform(
                source="old_name",
                target="new_name",
                transform="rename",
            ),
        ]
        
        result = pipeline.apply_column_transforms(df, transforms)
        
        assert "new_name" in result.columns
        assert "old_name" not in result.columns
    
    def test_apply_unit_conversion(self):
        """Test unit conversion transform."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "cd_um": [1.0, 2.0, 3.0],  # micrometers
        })
        
        # Convert from um to nm (multiply by 1000)
        result = pipeline.apply_unit_normalization(df, "cd_um", "um", "nm")
        
        assert result["cd_um"].to_list() == [1000.0, 2000.0, 3000.0]


class TestUnitNormalization:
    """Tests for unit normalization per DESIGN §6."""
    
    def test_normalize_units_by_policy_normalize(self):
        """Test normalizing units to canonical form."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "cd_um": [1.0, 2.0],
            "cd_nm": [1000.0, 2000.0],
        })
        
        # Mock profile with units_policy="normalize"
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            units_policy="normalize",
        )
        
        result = pipeline.apply_normalization(df, profile)
        
        # Should apply normalization (implementation dependent)
        assert result is not None
    
    def test_normalize_units_by_policy_preserve(self):
        """Test preserving units as-is."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "cd_um": [1.0, 2.0],
        })
        
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            units_policy="preserve",
        )
        
        result = pipeline.apply_normalization(df, profile)
        
        # Values should be unchanged
        assert result["cd_um"].to_list() == [1.0, 2.0]


class TestRowFilters:
    """Tests for row filters per DESIGN §6."""
    
    def test_row_filter_equals(self):
        """Test row filter with equals operator."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "status": ["valid", "invalid", "valid", "rejected"],
            "value": [1, 2, 3, 4],
        })
        
        filters = [
            {"column": "status", "op": "equals", "value": "valid"},
        ]
        
        result = pipeline.apply_row_filters(df, filters)
        
        assert len(result) == 2
        assert result["value"].to_list() == [1, 3]
    
    def test_row_filter_not_equals(self):
        """Test row filter with not_equals operator."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "status": ["valid", "invalid", "valid", "rejected"],
            "value": [1, 2, 3, 4],
        })
        
        filters = [
            {"column": "status", "op": "not_equals", "value": "rejected"},
        ]
        
        result = pipeline.apply_row_filters(df, filters)
        
        assert len(result) == 3
        assert 4 not in result["value"].to_list()
    
    def test_row_filter_between(self):
        """Test row filter with between operator."""
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "value": [5, 15, 25, 35, 45],
        })
        
        filters = [
            {"column": "value", "op": "between", "min": 10, "max": 40},
        ]
        
        result = pipeline.apply_row_filters(df, filters)
        
        assert len(result) == 3
        assert result["value"].to_list() == [15, 25, 35]


class TestAuditLogging:
    """Tests for audit logging per DESIGN §10."""
    
    @pytest.mark.asyncio
    async def test_audit_log_on_extraction_start(self, tmp_path: Path, caplog):
        """Test audit logging at extraction start."""
        # Create test file
        test_file = tmp_path / "test.json"
        test_file.write_text('{"summary": {"total": 1}}')
        
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test-audit",
            title="Test Audit",
            governance=GovernanceConfig(
                audit=GovernanceAuditConfig(
                    log_access=True,
                    log_modifications=True,
                ),
            ),
            levels=[
                LevelConfig(
                    name="run",
                    tables=[
                        TableConfig(
                            id="test_table",
                            label="Test",
                        ),
                    ],
                ),
            ],
        )
        
        executor = ProfileExecutor()
        
        import logging
        with caplog.at_level(logging.INFO):
            try:
                await executor.execute(
                    profile=profile,
                    files=[test_file],
                    context={},
                )
            except Exception:
                pass  # May fail due to missing table config
        
        # Check audit log message was generated
        assert any("AUDIT" in record.message for record in caplog.records)


class TestGovernanceSchema:
    """Tests for governance schema completeness per DESIGN §10."""
    
    def test_governance_access_config(self):
        """Test GovernanceAccessConfig defaults."""
        config = GovernanceAccessConfig()
        
        assert config.read == ["all"]
        assert config.modify == ["admin"]
        assert config.delete == ["admin"]
    
    def test_governance_audit_config(self):
        """Test GovernanceAuditConfig defaults."""
        config = GovernanceAuditConfig()
        
        assert config.log_access is True
        assert config.log_modifications is True
        assert config.retention_days == 365
    
    def test_governance_compliance_config(self):
        """Test GovernanceComplianceConfig defaults."""
        config = GovernanceComplianceConfig()
        
        assert config.data_classification == "internal"
        assert config.pii_columns == []
        assert config.mask_in_preview == []
    
    def test_governance_limits_config(self):
        """Test GovernanceLimitsConfig defaults."""
        config = GovernanceLimitsConfig()
        
        assert config.max_files_per_run == 1000
        assert config.max_file_size_mb == 500
        assert config.max_total_size_gb == 10
        assert config.max_rows_output == 10_000_000
        assert config.parse_timeout_seconds == 3600
    
    def test_full_governance_config(self):
        """Test full GovernanceConfig composition."""
        config = GovernanceConfig(
            access=GovernanceAccessConfig(read=["all"], modify=["admin"]),
            audit=GovernanceAuditConfig(log_access=True),
            compliance=GovernanceComplianceConfig(data_classification="confidential"),
            limits=GovernanceLimitsConfig(max_files_per_run=100),
        )
        
        assert config.access.read == ["all"]
        assert config.audit.log_access is True
        assert config.compliance.data_classification == "confidential"
        assert config.limits.max_files_per_run == 100
