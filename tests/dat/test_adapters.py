"""Tests for DAT file adapters.

Updated for contract-style async adapters per M1 refactor.
Per ADR-0011: Profile-Driven Extraction & AdapterFactory Pattern.
Per SPEC-DAT-0003: Adapter Interface & Registry specification.
"""
import json
import pytest
from pathlib import Path
import tempfile

import polars as pl

from apps.data_aggregator.backend.adapters import create_default_registry
from apps.data_aggregator.backend.adapters.json_adapter import JSONAdapter
from apps.data_aggregator.backend.adapters.csv_adapter import CSVAdapter
from shared.contracts.dat.adapter import ReadOptions


EXAMPLES_DIR = Path(__file__).parent.parent.parent / "apps" / "data_aggregator" / "backend" / "src" / "dat_aggregation" / "profiles" / "examples"


class TestAdapterRegistry:
    """Test adapter registry functionality."""

    def test_create_default_registry(self):
        """Test creating default registry with all adapters."""
        registry = create_default_registry()
        assert registry is not None
        
    def test_registry_has_json_adapter(self):
        """Test registry includes JSON adapter."""
        registry = create_default_registry()
        adapter = registry.get_adapter_for_file("test.json")
        assert adapter is not None
        assert adapter.metadata.adapter_id == "json"
        
    def test_registry_has_csv_adapter(self):
        """Test registry includes CSV adapter."""
        registry = create_default_registry()
        adapter = registry.get_adapter_for_file("test.csv")
        assert adapter is not None
        assert adapter.metadata.adapter_id == "csv"
        
    def test_registry_has_excel_adapter(self):
        """Test registry includes Excel adapter."""
        registry = create_default_registry()
        adapter = registry.get_adapter_for_file("test.xlsx")
        assert adapter is not None
        assert adapter.metadata.adapter_id == "excel"
        
    def test_registry_has_parquet_adapter(self):
        """Test registry includes Parquet adapter."""
        registry = create_default_registry()
        adapter = registry.get_adapter_for_file("test.parquet")
        assert adapter is not None
        assert adapter.metadata.adapter_id == "parquet"


class TestJSONAdapter:
    """Test JSON adapter functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create JSON adapter instance."""
        return JSONAdapter()
    
    def test_adapter_metadata(self, adapter):
        """Test adapter metadata is correct."""
        assert adapter.metadata.adapter_id == "json"
        assert ".json" in adapter.metadata.file_extensions
        assert ".jsonl" in adapter.metadata.file_extensions
        
    def test_adapter_capabilities(self, adapter):
        """Test adapter capabilities are set correctly."""
        caps = adapter.metadata.capabilities
        assert caps.supports_streaming is True
        assert caps.supports_schema_inference is True
        
    @pytest.mark.asyncio
    async def test_probe_schema_simple_array(self, adapter):
        """Test probing schema from simple JSON array."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"id": 1, "name": "test1", "value": 10.5},
                {"id": 2, "name": "test2", "value": 20.5},
            ], f)
            f.flush()
            
            result = await adapter.probe_schema(f.name)
            
            assert len(result.columns) >= 3
            column_names = [c.name for c in result.columns]
            assert "id" in column_names
            assert "name" in column_names
            assert "value" in column_names
            
    @pytest.mark.asyncio
    async def test_read_simple_json_array(self, adapter):
        """Test reading simple JSON array."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([
                {"id": 1, "name": "test1", "value": 10.5},
                {"id": 2, "name": "test2", "value": 20.5},
            ], f)
            f.flush()
            
            df, result = await adapter.read_dataframe(f.name)
            
            assert len(df) == 2
            assert "id" in df.columns
            assert "name" in df.columns
            assert "value" in df.columns
            assert result.rows_read == 2
            
    @pytest.mark.asyncio
    async def test_read_single_json_object(self, adapter):
        """Test reading single JSON object."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump({"id": 1, "name": "test", "value": 10.5}, f)
            f.flush()
            
            df, result = await adapter.read_dataframe(f.name)
            
            assert len(df) == 1
            assert df["id"][0] == 1
            assert df["name"][0] == "test"


class TestCSVAdapter:
    """Test CSV adapter functionality."""
    
    @pytest.fixture
    def adapter(self):
        """Create CSV adapter instance."""
        return CSVAdapter()
    
    def test_adapter_metadata(self, adapter):
        """Test adapter metadata is correct."""
        assert adapter.metadata.adapter_id == "csv"
        assert ".csv" in adapter.metadata.file_extensions
        
    @pytest.mark.asyncio
    async def test_read_simple_csv(self, adapter):
        """Test reading simple CSV file."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,name,value\n")
            f.write("1,test1,10.5\n")
            f.write("2,test2,20.5\n")
            f.flush()
            
            df, result = await adapter.read_dataframe(f.name)
            
            assert len(df) == 2
            assert "id" in df.columns
            assert "name" in df.columns
            assert "value" in df.columns
            assert result.rows_read == 2


class TestAdapterIntegration:
    """Integration tests for adapter registry."""
    
    @pytest.mark.asyncio
    async def test_registry_read_json(self):
        """Test reading JSON through registry."""
        registry = create_default_registry()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump([{"id": 1, "value": 100}], f)
            f.flush()
            
            adapter = registry.get_adapter_for_file(f.name)
            df, result = await adapter.read_dataframe(f.name)
            
            assert len(df) == 1
            assert df["id"][0] == 1
            
    @pytest.mark.asyncio
    async def test_registry_read_csv(self):
        """Test reading CSV through registry."""
        registry = create_default_registry()
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            f.write("id,value\n1,100\n")
            f.flush()
            
            adapter = registry.get_adapter_for_file(f.name)
            df, result = await adapter.read_dataframe(f.name)
            
            assert len(df) == 1
