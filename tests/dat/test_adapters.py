"""Tests for DAT file adapters."""
import json
import pytest
from pathlib import Path
import tempfile

import polars as pl

from apps.data_aggregator.backend.src.dat_aggregation.adapters.factory import AdapterFactory
from apps.data_aggregator.backend.src.dat_aggregation.adapters.json_adapter import (
    JSONAdapter,
    extract_table_from_json,
)


EXAMPLES_DIR = Path(__file__).parent.parent.parent / "apps" / "data_aggregator" / "backend" / "src" / "dat_aggregation" / "profiles" / "examples"


class TestJSONAdapter:
    """Test JSON adapter functionality."""
    
    def test_can_handle_json(self):
        """Test JSON adapter recognizes .json files."""
        assert JSONAdapter.can_handle(Path("test.json"))
        assert JSONAdapter.can_handle(Path("data.JSON"))
        assert not JSONAdapter.can_handle(Path("test.csv"))
        assert not JSONAdapter.can_handle(Path("test.xlsx"))
    
    def test_read_simple_json_array(self):
        """Test reading simple JSON array."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"id": 1, "name": "test1", "value": 10.5},
                {"id": 2, "name": "test2", "value": 20.5},
            ], f)
            f.flush()
            
            df = JSONAdapter.read(Path(f.name))
            
            assert len(df) == 2
            assert "id" in df.columns
            assert "name" in df.columns
            assert "value" in df.columns
    
    def test_read_simple_json_object(self):
        """Test reading simple JSON object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"id": 1, "name": "test", "value": 10.5}, f)
            f.flush()
            
            df = JSONAdapter.read(Path(f.name))
            
            assert len(df) == 1
            assert df["id"][0] == 1
            assert df["name"][0] == "test"
    
    def test_read_with_json_path(self):
        """Test reading with JSON path extraction."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "metadata": {"version": "1.0"},
                "data": [
                    {"x": 1, "y": 2},
                    {"x": 3, "y": 4},
                ]
            }, f)
            f.flush()
            
            df = JSONAdapter.read(Path(f.name), json_path="$.data")
            
            assert len(df) == 2
            assert "x" in df.columns
            assert "y" in df.columns
    
    def test_read_headers_data_format(self):
        """Test reading headers + data format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "columns": ["param", "mean", "std"],
                "values": [
                    ["CD", 24.5, 0.8],
                    ["Height", 48.0, 1.2],
                ]
            }, f)
            f.flush()
            
            df = JSONAdapter.read(
                Path(f.name),
                headers_key="columns",
                data_key="values"
            )
            
            assert len(df) == 2
            assert list(df.columns) == ["param", "mean", "std"]
            assert df["param"][0] == "CD"
            assert df["mean"][0] == 24.5
    
    def test_read_nested_path_with_headers_data(self):
        """Test reading nested path with headers + data format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "result": {
                    "statistics": {
                        "columns": ["name", "value"],
                        "values": [["test", 100]]
                    }
                }
            }, f)
            f.flush()
            
            df = JSONAdapter.read(
                Path(f.name),
                json_path="$.result.statistics",
                headers_key="columns",
                data_key="values"
            )
            
            assert len(df) == 1
            assert df["name"][0] == "test"
            assert df["value"][0] == 100
    
    def test_get_tables_from_nested_json(self):
        """Test discovering tables from nested JSON."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({
                "summary": {"total": 10, "valid": 8},
                "statistics": {
                    "columns": ["a", "b"],
                    "data": [[1, 2]]
                },
                "items": [
                    {"id": 1, "value": 10},
                    {"id": 2, "value": 20},
                ]
            }, f)
            f.flush()
            
            tables = JSONAdapter.get_tables(Path(f.name))
            
            assert len(tables) > 0
            # Should find statistics (headers+data) and items (array of objects)
            assert any("statistics" in t for t in tables)
            assert any("items" in t for t in tables)
    
    def test_get_preview(self):
        """Test getting preview of JSON data."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": i, "value": i * 10} for i in range(200)], f)
            f.flush()
            
            preview = JSONAdapter.get_preview(Path(f.name), rows=50)
            
            assert len(preview) == 50
    
    def test_extract_path_with_array_index(self):
        """Test JSONPath extraction with array indexing."""
        data = {
            "items": [
                {"name": "first"},
                {"name": "second"},
            ]
        }
        
        result = JSONAdapter._extract_path(data, "$.items[0]")
        assert result["name"] == "first"
        
        result = JSONAdapter._extract_path(data, "$.items[1]")
        assert result["name"] == "second"
    
    def test_extract_path_with_wildcard(self):
        """Test JSONPath extraction with wildcard."""
        data = {
            "items": [
                {"name": "first"},
                {"name": "second"},
            ]
        }
        
        result = JSONAdapter._extract_path(data, "$.items[*]")
        assert isinstance(result, list)
        assert len(result) == 2


class TestJSONAdapterWithExampleData:
    """Test JSON adapter with actual example data files."""
    
    @pytest.fixture
    def example_data_path(self):
        """Get path to example data file."""
        return EXAMPLES_DIR / "LOTABC12345_W01_CDSEM001_20251227_measurement.json"
    
    def test_can_load_example_file(self, example_data_path):
        """Test that example file can be loaded."""
        if not example_data_path.exists():
            pytest.skip("Example data file not found")
        
        assert JSONAdapter.can_handle(example_data_path)
    
    def test_get_tables_from_example(self, example_data_path):
        """Test discovering tables from example file."""
        if not example_data_path.exists():
            pytest.skip("Example data file not found")
        
        tables = JSONAdapter.get_tables(example_data_path)
        
        assert len(tables) > 0
    
    def test_read_summary_from_example(self, example_data_path):
        """Test reading summary section from example."""
        if not example_data_path.exists():
            pytest.skip("Example data file not found")
        
        df = JSONAdapter.read(example_data_path, json_path="$.summary")
        
        assert len(df) == 1
        assert "total_images" in df.columns
        assert "mean_cd" in df.columns
    
    def test_read_statistics_from_example(self, example_data_path):
        """Test reading statistics section from example."""
        if not example_data_path.exists():
            pytest.skip("Example data file not found")
        
        df = JSONAdapter.read(
            example_data_path,
            json_path="$.statistics",
            headers_key="columns",
            data_key="values"
        )
        
        assert len(df) > 0
        assert "parameter" in df.columns
        assert "mean" in df.columns
    
    def test_read_images_from_example(self, example_data_path):
        """Test reading images measurements from example."""
        if not example_data_path.exists():
            pytest.skip("Example data file not found")
        
        # Read just the first image's measurements using headers_data format
        df = JSONAdapter.read(
            example_data_path,
            json_path="$.images[0].measurements",
            headers_key="columns",
            data_key="values"
        )
        
        assert len(df) > 0
        assert "image_id" in df.columns


class TestExtractTableFromJSON:
    """Test profile-driven table extraction."""
    
    def test_extract_flat_object(self):
        """Test extracting flat object."""
        data = {
            "summary": {
                "total": 100,
                "valid": 95,
                "mean": 24.5
            }
        }
        
        table_config = {
            "select": {
                "strategy": "flat_object",
                "path": "$.summary"
            }
        }
        
        df = extract_table_from_json(data, table_config)
        
        assert len(df) == 1
        assert df["total"][0] == 100
        assert df["mean"][0] == 24.5
    
    def test_extract_headers_data(self):
        """Test extracting headers + data format."""
        data = {
            "statistics": {
                "columns": ["param", "value", "unit"],
                "values": [
                    ["CD", 24.5, "nm"],
                    ["Height", 48.0, "nm"],
                ]
            }
        }
        
        table_config = {
            "select": {
                "strategy": "headers_data",
                "path": "$.statistics",
                "headers_key": "columns",
                "data_key": "values"
            }
        }
        
        df = extract_table_from_json(data, table_config)
        
        assert len(df) == 2
        assert list(df.columns) == ["param", "value", "unit"]
    
    def test_extract_with_repeat_over(self):
        """Test extracting with repeat_over iteration."""
        data = {
            "sites": [
                {
                    "cd_data": {
                        "headers": ["site_id", "value"],
                        "rows": [["SITE01", 24.1]]
                    }
                },
                {
                    "cd_data": {
                        "headers": ["site_id", "value"],
                        "rows": [["SITE02", 24.3]]
                    }
                }
            ]
        }
        
        table_config = {
            "select": {
                "strategy": "headers_data",
                "path": "$.sites[{site_index}].cd_data",
                "headers_key": "headers",
                "data_key": "rows",
                "repeat_over": {
                    "path": "$.sites",
                    "as": "site_index"
                }
            }
        }
        
        df = extract_table_from_json(data, table_config)
        
        assert len(df) == 2
        assert df["site_id"][0] == "SITE01"
        assert df["site_id"][1] == "SITE02"


class TestAdapterFactory:
    """Test adapter factory functionality."""
    
    def test_get_supported_extensions(self):
        """Test getting all supported extensions."""
        extensions = AdapterFactory.get_supported_extensions()
        
        assert ".json" in extensions
        assert ".csv" in extensions
        assert ".xlsx" in extensions
        assert ".parquet" in extensions
    
    def test_get_adapter_for_json(self):
        """Test getting adapter for JSON file."""
        adapter = AdapterFactory.get_adapter(Path("test.json"))
        assert adapter == JSONAdapter
    
    def test_get_adapter_for_csv(self):
        """Test getting adapter for CSV file."""
        from apps.data_aggregator.backend.src.dat_aggregation.adapters.csv_adapter import CSVAdapter
        adapter = AdapterFactory.get_adapter(Path("test.csv"))
        assert adapter == CSVAdapter
    
    def test_get_adapter_unsupported(self):
        """Test error for unsupported file type."""
        with pytest.raises(ValueError, match="No adapter found"):
            AdapterFactory.get_adapter(Path("test.unsupported"))
    
    def test_read_json_file(self):
        """Test reading JSON file through factory."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1, "value": 100}], f)
            f.flush()
            
            df = AdapterFactory.read_file(Path(f.name))
            
            assert len(df) == 1
            assert df["id"][0] == 1
