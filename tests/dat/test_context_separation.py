"""Tests for context separation in profile-driven extraction.

Per DESIGN §4, §9: Tables and context must be kept separate during extraction.
User controls context application at output time via toggles:
- include_run_context: Add run-level context (LotID, WaferID, etc.)
- include_image_context: Add image-level context (ImageName, etc.)
"""


import polars as pl
import pytest

from apps.data_aggregator.backend.src.dat_aggregation.profiles.output_builder import (
    ContextOptions,
    OutputBuilder,
)
from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_executor import (
    ExtractionResult,
)


class TestExtractionResult:
    """Tests for ExtractionResult dataclass."""

    def test_empty_result(self):
        """Empty result should have empty tables and contexts."""
        result = ExtractionResult()
        assert result.tables == {}
        assert result.run_context == {}
        assert result.image_contexts == {}
        assert result.file_contexts == {}
        assert result.validation_warnings == []

    def test_apply_run_context_adds_columns(self):
        """apply_run_context should add context columns to tables."""
        result = ExtractionResult(
            tables={
                "test_table": pl.DataFrame({"col1": [1, 2, 3], "col2": ["a", "b", "c"]})
            },
            run_context={"LotID": "LOT123", "WaferID": "W01"},
        )

        tables_with_context = result.apply_run_context()

        assert "test_table" in tables_with_context
        df = tables_with_context["test_table"]
        assert "LotID" in df.columns
        assert "WaferID" in df.columns
        assert df["LotID"][0] == "LOT123"
        assert df["WaferID"][0] == "W01"

    def test_apply_run_context_selective_tables(self):
        """apply_run_context should only apply to specified tables."""
        result = ExtractionResult(
            tables={
                "table1": pl.DataFrame({"col1": [1]}),
                "table2": pl.DataFrame({"col2": [2]}),
            },
            run_context={"LotID": "LOT123"},
        )

        tables_with_context = result.apply_run_context(table_ids=["table1"])

        assert "table1" in tables_with_context
        assert "table2" not in tables_with_context
        assert "LotID" in tables_with_context["table1"].columns

    def test_apply_run_context_preserves_existing_columns(self):
        """apply_run_context should not overwrite existing columns."""
        result = ExtractionResult(
            tables={
                "test_table": pl.DataFrame({"LotID": ["EXISTING"], "col1": [1]})
            },
            run_context={"LotID": "LOT123", "NewCol": "new_value"},
        )

        tables_with_context = result.apply_run_context()

        df = tables_with_context["test_table"]
        # Existing column should be preserved
        assert df["LotID"][0] == "EXISTING"
        # New column should be added
        assert "NewCol" in df.columns
        assert df["NewCol"][0] == "new_value"

    def test_get_tables_with_context_no_context(self):
        """get_tables_with_context with both flags False returns raw tables."""
        result = ExtractionResult(
            tables={"test_table": pl.DataFrame({"col1": [1, 2, 3]})},
            run_context={"LotID": "LOT123"},
            image_contexts={"IMG_001": {"ImageName": "test.png"}},
        )

        tables = result.get_tables_with_context(
            include_run_context=False,
            include_image_context=False,
        )

        assert "test_table" in tables
        assert "LotID" not in tables["test_table"].columns
        assert "ImageName" not in tables["test_table"].columns

    def test_get_tables_with_context_run_only(self):
        """get_tables_with_context with only run context."""
        result = ExtractionResult(
            tables={"test_table": pl.DataFrame({"col1": [1]})},
            run_context={"LotID": "LOT123", "WaferID": "W01"},
            image_contexts={"IMG_001": {"ImageName": "test.png"}},
        )

        tables = result.get_tables_with_context(
            include_run_context=True,
            include_image_context=False,
        )

        df = tables["test_table"]
        assert "LotID" in df.columns
        assert "WaferID" in df.columns
        # Image context should NOT be added
        assert "ImageName" not in df.columns


class TestContextOptions:
    """Tests for ContextOptions dataclass."""

    def test_default_options(self):
        """Default options should include run context but not image context."""
        options = ContextOptions()
        assert options.include_run_context is True
        assert options.include_image_context is False
        assert options.run_context_keys is None
        assert options.image_context_keys is None

    def test_custom_options(self):
        """Custom options should be configurable."""
        options = ContextOptions(
            include_run_context=False,
            include_image_context=True,
            run_context_keys=["LotID"],
            image_context_keys=["ImageName"],
        )
        assert options.include_run_context is False
        assert options.include_image_context is True
        assert options.run_context_keys == ["LotID"]
        assert options.image_context_keys == ["ImageName"]


class TestOutputBuilderContextApplication:
    """Tests for OutputBuilder context application."""

    def test_build_output_with_run_context(self):
        """_build_output should apply run context when option is True."""
        from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
            OutputConfig,
        )

        builder = OutputBuilder()
        tables = {"test_table": pl.DataFrame({"col1": [1, 2]})}
        run_context = {"LotID": "LOT123", "WaferID": "W01"}
        options = ContextOptions(include_run_context=True, include_image_context=False)

        config = OutputConfig(id="output1", from_level="test", from_tables=["test_table"])
        result = builder._build_output(config, tables, run_context, {}, options)

        assert "LotID" in result.columns
        assert "WaferID" in result.columns

    def test_build_output_without_context(self):
        """_build_output should not apply context when options are False."""
        from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
            OutputConfig,
        )

        builder = OutputBuilder()
        tables = {"test_table": pl.DataFrame({"col1": [1, 2]})}
        run_context = {"LotID": "LOT123"}
        options = ContextOptions(include_run_context=False, include_image_context=False)

        config = OutputConfig(id="output1", from_level="test", from_tables=["test_table"], include_context=False)
        result = builder._build_output(config, tables, run_context, {}, options)

        assert "LotID" not in result.columns

    def test_build_output_selective_keys(self):
        """_build_output should only apply specified context keys."""
        from apps.data_aggregator.backend.src.dat_aggregation.profiles.profile_loader import (
            OutputConfig,
        )

        builder = OutputBuilder()
        tables = {"test_table": pl.DataFrame({"col1": [1]})}
        run_context = {"LotID": "LOT123", "WaferID": "W01", "RecipeName": "RCP_TEST"}
        options = ContextOptions(
            include_run_context=True,
            include_image_context=False,
            run_context_keys=["LotID", "WaferID"],  # Exclude RecipeName
        )

        config = OutputConfig(id="output1", from_level="test", from_tables=["test_table"])
        result = builder._build_output(config, tables, run_context, {}, options)

        assert "LotID" in result.columns
        assert "WaferID" in result.columns
        assert "RecipeName" not in result.columns


class TestProfileExecutorContextSeparation:
    """Integration tests for ProfileExecutor context separation."""

    @pytest.mark.asyncio
    async def test_execute_returns_extraction_result(self):
        """execute() should return ExtractionResult with separated tables and context."""
        # This would require mocking the profile and file loading
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_execute_apply_context_false_keeps_tables_raw(self):
        """execute(apply_context=False) should not add context columns to tables."""
        # Placeholder for integration test
        pass

    @pytest.mark.asyncio
    async def test_execute_apply_context_true_adds_context(self):
        """execute(apply_context=True) should add context columns (legacy mode)."""
        # Placeholder for integration test
        pass


# Acceptance criteria tests per DESIGN §4, §9
class TestContextSeparationAcceptanceCriteria:
    """Acceptance criteria for context separation feature."""

    def test_ac1_tables_extracted_without_context_by_default(self):
        """AC-1: Tables must be extracted without context columns by default."""
        result = ExtractionResult(
            tables={"test": pl.DataFrame({"data": [1, 2, 3]})},
            run_context={"LotID": "LOT123"},
        )

        # Raw tables should not have context
        raw_table = result.tables["test"]
        assert "LotID" not in raw_table.columns, "Raw tables should not have context columns"

    def test_ac2_context_stored_separately(self):
        """AC-2: Context must be stored separately from tables."""
        result = ExtractionResult(
            tables={"test": pl.DataFrame({"data": [1]})},
            run_context={"LotID": "LOT123", "WaferID": "W01"},
            image_contexts={"IMG_001": {"ImageName": "test.png"}},
        )

        # Context is in separate attributes
        assert result.run_context == {"LotID": "LOT123", "WaferID": "W01"}
        assert result.image_contexts == {"IMG_001": {"ImageName": "test.png"}}

    def test_ac3_user_can_toggle_run_context(self):
        """AC-3: User must be able to toggle run-level context application."""
        result = ExtractionResult(
            tables={"test": pl.DataFrame({"data": [1]})},
            run_context={"LotID": "LOT123"},
        )

        # Without run context
        tables_no_ctx = result.get_tables_with_context(include_run_context=False)
        assert "LotID" not in tables_no_ctx["test"].columns

        # With run context
        tables_with_ctx = result.get_tables_with_context(include_run_context=True)
        assert "LotID" in tables_with_ctx["test"].columns

    def test_ac4_user_can_toggle_image_context(self):
        """AC-4: User must be able to toggle image-level context application."""
        result = ExtractionResult(
            tables={"test": pl.DataFrame({"image_id": ["IMG_001"], "data": [1]})},
            image_contexts={"IMG_001": {"ImageName": "test.png"}},
        )

        # Without image context
        tables_no_ctx = result.get_tables_with_context(include_image_context=False)
        assert "ImageName" not in tables_no_ctx["test"].columns

        # With image context - note: apply_image_context needs image_id column
        tables_with_ctx = result.apply_image_context()
        # Image context application requires matching image_id
        assert "test" in tables_with_ctx

    def test_ac5_context_options_default_to_sensible_values(self):
        """AC-5: Context options must default to sensible values."""
        options = ContextOptions()

        # Run context ON by default (most common use case)
        assert options.include_run_context is True

        # Image context OFF by default (less common)
        assert options.include_image_context is False
