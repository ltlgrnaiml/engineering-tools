"""Unit tests for ProfileExecutor and extraction strategies.

Per ADR-0011: Tests verify profile-driven extraction produces correct results.
"""

import json
from pathlib import Path

import polars as pl
import pytest

from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
    load_profile,
    get_profile_by_id,
    ContextDefaults,
    ContentPattern,
    RegexPattern,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_executor import (
    ProfileExecutor,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.strategies import (
    FlatObjectStrategy,
    HeadersDataStrategy,
    ArrayOfObjectsStrategy,
    RepeatOverStrategy,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.strategies.base import (
    SelectConfig,
    RepeatOverConfig,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.context_extractor import (
    ContextExtractor,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.validation_engine import (
    ValidationEngine,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.transform_pipeline import (
    TransformPipeline,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.output_builder import (
    OutputBuilder,
)


# Test fixture path
FIXTURE_PATH = Path(__file__).parent.parent.parent.parent / "fixtures" / "dat" / "cdsem_sample.json"


@pytest.fixture
def sample_data() -> dict:
    """Load sample CD-SEM data."""
    with open(FIXTURE_PATH, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def cdsem_profile():
    """Load CD-SEM profile."""
    return get_profile_by_id("cdsem-metrology-v1")


class TestFlatObjectStrategy:
    """Tests for FlatObjectStrategy."""
    
    def test_extract_summary(self, sample_data: dict):
        """Test extracting flat object as single row."""
        strategy = FlatObjectStrategy()
        config = SelectConfig(
            strategy="flat_object",
            path="$.summary",
        )
        
        df = strategy.extract(sample_data, config, {})
        
        assert len(df) == 1
        assert "total_images" in df.columns
        assert "mean_cd" in df.columns
        assert df["total_images"][0] == 50
        assert df["mean_cd"][0] == 45.2
    
    def test_extract_diagnostics(self, sample_data: dict):
        """Test extracting diagnostics as flat object."""
        strategy = FlatObjectStrategy()
        config = SelectConfig(
            strategy="flat_object",
            path="$.diagnostics",
        )
        
        df = strategy.extract(sample_data, config, {})
        
        assert len(df) == 1
        assert "beam_current" in df.columns
        assert "focus_score" in df.columns
        assert df["focus_score"][0] == 0.95
    
    def test_missing_path_returns_empty(self, sample_data: dict):
        """Test that missing path returns empty DataFrame."""
        strategy = FlatObjectStrategy()
        config = SelectConfig(
            strategy="flat_object",
            path="$.nonexistent",
        )
        
        df = strategy.extract(sample_data, config, {})
        
        assert df.is_empty()


class TestHeadersDataStrategy:
    """Tests for HeadersDataStrategy."""
    
    def test_extract_statistics(self, sample_data: dict):
        """Test extracting headers+data as DataFrame."""
        strategy = HeadersDataStrategy()
        config = SelectConfig(
            strategy="headers_data",
            path="$.statistics",
            headers_key="columns",
            data_key="values",
        )
        
        df = strategy.extract(sample_data, config, {})
        
        assert len(df) == 4  # 4 parameters
        assert "parameter" in df.columns
        assert "mean" in df.columns
        assert df["parameter"].to_list() == ["cd_left", "cd_right", "cd_average", "height"]
    
    def test_extract_site_cd_data(self, sample_data: dict):
        """Test extracting site-level CD data."""
        strategy = HeadersDataStrategy()
        config = SelectConfig(
            strategy="headers_data",
            path="$.sites[0].cd_data",
            headers_key="headers",
            data_key="rows",
        )
        
        df = strategy.extract(sample_data, config, {})
        
        assert len(df) == 4  # 4 rows in first site
        assert "x_position" in df.columns
        assert "cd_value" in df.columns


class TestRepeatOverStrategy:
    """Tests for RepeatOverStrategy."""
    
    def test_repeat_over_sites(self, sample_data: dict):
        """Test iterating over sites."""
        strategy = RepeatOverStrategy()
        config = SelectConfig(
            strategy="headers_data",
            path="$.sites[{site_index}].cd_data",
            headers_key="headers",
            data_key="rows",
            repeat_over=RepeatOverConfig(
                path="$.sites",
                as_var="site_index",
                inject_fields={"site_id": "$.site_id", "site_name": "$.name"},
            ),
        )
        
        df = strategy.extract(sample_data, config, {})
        
        # 4 + 4 + 2 = 10 rows from 3 sites
        assert len(df) == 10
        assert "site_id" in df.columns
        assert "site_name" in df.columns
        # Verify site_id is injected
        site_ids = df["site_id"].unique().to_list()
        assert "S01" in site_ids
        assert "S02" in site_ids
        assert "S03" in site_ids


class TestContextExtractor:
    """Tests for ContextExtractor."""
    
    def test_extract_from_filename(self, cdsem_profile):
        """Test regex extraction from filename."""
        if cdsem_profile is None:
            pytest.skip("CD-SEM profile not found")
        
        extractor = ContextExtractor()
        file_path = Path("LOTABC12345_W01_CDSEM001_measurement.json")
        
        context = extractor.extract(
            profile=cdsem_profile,
            file_path=file_path,
        )
        
        assert context.get("lot_id") == "LOTABC12345"
        assert context.get("wafer_id") == "W01"
    
    def test_user_override_priority(self, cdsem_profile):
        """Test that user overrides have highest priority."""
        if cdsem_profile is None:
            pytest.skip("CD-SEM profile not found")
        
        extractor = ContextExtractor()
        file_path = Path("LOTABC12345_W01_measurement.json")
        
        context = extractor.extract(
            profile=cdsem_profile,
            file_path=file_path,
            user_overrides={"lot_id": "OVERRIDE_LOT"},
        )
        
        assert context["lot_id"] == "OVERRIDE_LOT"

    def test_content_patterns_override_defaults(self, sample_data: dict):
        """JSONPath content patterns override defaults."""
        extractor = ContextExtractor()
        profile = get_profile_by_id("cdsem-metrology-v1")
        assert profile is not None
        profile.context_defaults = ContextDefaults(
            defaults={"total_images": 0},
            regex_patterns=[
                RegexPattern(field="total_images", pattern=r"(?P<total_images>999)", scope="filename")
            ],
            content_patterns=[
                ContentPattern(field="total_images", path="$.summary.total_images", required=True)
            ],
            allow_user_override=[],
        )
        context = extractor.extract(
            profile=profile,
            file_path=Path("any.json"),
            file_content=sample_data,
            user_overrides=None,
        )
        assert context["total_images"] == 50

    def test_user_override_allowlist(self):
        """User overrides are restricted to allow_user_override list."""
        extractor = ContextExtractor()
        profile = get_profile_by_id("cdsem-metrology-v1")
        assert profile is not None
        profile.context_defaults = ContextDefaults(
            defaults={},
            regex_patterns=[],
            content_patterns=[],
            allow_user_override=["wafer_id"],
        )
        context = extractor.extract(
            profile=profile,
            file_path=Path("LOTABC12345_W01_measurement.json"),
            file_content=None,
            user_overrides={"wafer_id": "W99", "lot_id": "BLOCKED"},
        )
        assert context["wafer_id"] == "W99"
        assert "lot_id" not in context


class TestValidationEngine:
    """Tests for ValidationEngine."""
    
    def test_validate_stable_columns_pass(self):
        """Test validation passes when all stable columns present."""
        engine = ValidationEngine()
        
        from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
            TableConfig,
        )
        
        df = pl.DataFrame({
            "total_images": [50],
            "mean_cd": [45.2],
            "sigma_cd": [1.3],
            "extra_col": ["ignored"],
        })
        
        table_config = TableConfig(
            id="test_table",
            label="Test Table",
            stable_columns=["total_images", "mean_cd", "sigma_cd"],
            stable_columns_mode="warn",
            stable_columns_subset=True,
        )
        
        result = engine.validate_table(df, table_config)
        
        assert result.valid
        assert len(result.errors) == 0
        assert len(result.missing_columns) == 0
    
    def test_validate_missing_column_warn(self):
        """Test validation warns on missing column."""
        engine = ValidationEngine()
        
        from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
            TableConfig,
        )
        
        df = pl.DataFrame({
            "total_images": [50],
            "mean_cd": [45.2],
        })
        
        table_config = TableConfig(
            id="test_table",
            label="Test Table",
            stable_columns=["total_images", "mean_cd", "sigma_cd"],
            stable_columns_mode="warn",
            stable_columns_subset=True,
        )
        
        result = engine.validate_table(df, table_config)
        
        assert result.valid  # warn mode still valid
        assert len(result.warnings) == 1
        assert "sigma_cd" in result.missing_columns


class TestTransformPipeline:
    """Tests for TransformPipeline."""
    
    def test_replace_nan_values(self):
        """Test NaN value replacement."""
        from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
            DATProfile,
        )
        
        pipeline = TransformPipeline()
        
        df = pl.DataFrame({
            "value": ["1.0", "N/A", "3.0", "NA", "5.0"],
        })
        
        # Create minimal profile with nan_values
        profile = DATProfile(
            schema_version="1.0.0",
            version=1,
            profile_id="test",
            title="Test",
            nan_values=["N/A", "NA"],
        )
        
        result = pipeline.apply_normalization(df, profile)
        
        # N/A and NA should be replaced with null
        assert result["value"][1] is None
        assert result["value"][3] is None


class TestOutputBuilder:
    """Tests for OutputBuilder."""
    
    def test_combine_all_tables(self):
        """Test combining multiple tables."""
        builder = OutputBuilder()
        
        tables = {
            "table1": pl.DataFrame({"a": [1, 2], "b": [3, 4]}),
            "table2": pl.DataFrame({"a": [5, 6], "c": [7, 8]}),
        }
        
        combined = builder.combine_all_tables(tables)
        
        assert len(combined) == 4
        assert "__table_id__" in combined.columns
        assert "a" in combined.columns
        assert "b" in combined.columns
        assert "c" in combined.columns


@pytest.mark.asyncio
class TestProfileExecutor:
    """Integration tests for ProfileExecutor."""
    
    async def test_execute_profile(self, sample_data: dict, cdsem_profile, tmp_path: Path):
        """Test full profile execution."""
        if cdsem_profile is None:
            pytest.skip("CD-SEM profile not found")
        
        # Write sample data to temp file
        sample_file = tmp_path / "LOTABC12345_W01_measurement.json"
        with open(sample_file, "w", encoding="utf-8") as f:
            json.dump(sample_data, f)
        
        executor = ProfileExecutor()
        results = await executor.execute(
            profile=cdsem_profile,
            files=[sample_file],
            context={},
            selected_tables=["run_summary", "run_statistics"],
        )
        
        assert "run_summary" in results
        assert "run_statistics" in results
        
        # Verify run_summary is single row (flat_object)
        assert len(results["run_summary"]) == 1
        
        # Verify run_statistics has multiple rows (headers_data)
        assert len(results["run_statistics"]) == 4
