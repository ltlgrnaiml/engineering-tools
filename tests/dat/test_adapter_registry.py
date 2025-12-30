"""Unit tests for AdapterRegistry.

Per SPEC-0026: Adapter Interface & Registry specification.
Tests AC-2: AdapterRegistry Requirements from ACCEPTANCE_CRITERIA_ADAPTERS.md
"""

import pytest

from apps.data_aggregator.backend.adapters import (
    AdapterNotFoundError,
    AdapterRegistry,
    CSVAdapter,
    ExcelAdapter,
    JSONAdapter,
    create_default_registry,
)
from shared.contracts.dat.adapter import AdapterMetadata


class TestAdapterRegistryRegistration:
    """Test AC-2.1: Registration requirements."""

    def test_register_adds_adapter_to_registry(self) -> None:
        """AC-2.1.1: register() adds adapter to registry."""
        registry = AdapterRegistry()
        adapter = CSVAdapter()

        registry.register(adapter)

        assert "csv" in registry
        assert len(registry) == 1

    def test_register_maps_file_extensions(self) -> None:
        """AC-2.1.2: register() maps file extensions to adapter_id."""
        registry = AdapterRegistry()
        adapter = CSVAdapter()

        registry.register(adapter)

        state = registry.get_state()
        assert ".csv" in state.extension_map
        assert ".tsv" in state.extension_map
        assert state.extension_map[".csv"] == "csv"
        assert state.extension_map[".tsv"] == "csv"

    def test_register_maps_mime_types(self) -> None:
        """AC-2.1.3: register() maps MIME types to adapter_id."""
        registry = AdapterRegistry()
        adapter = CSVAdapter()

        registry.register(adapter)

        state = registry.get_state()
        assert "text/csv" in state.mime_map
        assert state.mime_map["text/csv"] == "csv"

    def test_register_duplicate_raises_value_error(self) -> None:
        """AC-2.1.4: Duplicate adapter_id raises ValueError."""
        registry = AdapterRegistry()
        adapter1 = CSVAdapter()
        adapter2 = CSVAdapter()

        registry.register(adapter1)

        with pytest.raises(ValueError, match="already registered"):
            registry.register(adapter2)


class TestAdapterRegistryLookup:
    """Test AC-2.2: Lookup requirements."""

    def test_get_adapter_returns_correct_adapter(self) -> None:
        """AC-2.2.1: get_adapter(adapter_id) returns correct adapter."""
        registry = AdapterRegistry()
        csv_adapter = CSVAdapter()
        registry.register(csv_adapter)

        result = registry.get_adapter("csv")

        assert result is csv_adapter

    def test_get_adapter_raises_for_unknown_id(self) -> None:
        """AC-2.2.2: get_adapter() raises AdapterNotFoundError for unknown ID."""
        registry = AdapterRegistry()

        with pytest.raises(AdapterNotFoundError) as exc_info:
            registry.get_adapter("unknown")

        assert exc_info.value.adapter_id == "unknown"

    def test_get_adapter_for_file_selects_by_extension(self) -> None:
        """AC-2.2.3: get_adapter_for_file(path) selects by extension."""
        registry = create_default_registry()

        csv_adapter = registry.get_adapter_for_file("data.csv")
        tsv_adapter = registry.get_adapter_for_file("data.tsv")
        xlsx_adapter = registry.get_adapter_for_file("data.xlsx")
        json_adapter = registry.get_adapter_for_file("data.json")

        assert csv_adapter.metadata.adapter_id == "csv"
        assert tsv_adapter.metadata.adapter_id == "csv"
        assert xlsx_adapter.metadata.adapter_id == "excel"
        assert json_adapter.metadata.adapter_id == "json"

    def test_get_adapter_for_file_prefers_mime_type(self) -> None:
        """AC-2.2.4: get_adapter_for_file(path, mime_type) prefers MIME type."""
        registry = create_default_registry()

        # File has .json extension but we specify CSV mime type
        adapter = registry.get_adapter_for_file("data.json", mime_type="text/csv")

        assert adapter.metadata.adapter_id == "csv"

    def test_get_adapter_for_file_raises_for_unknown_format(self) -> None:
        """AC-2.2.5: get_adapter_for_file() raises AdapterNotFoundError."""
        registry = create_default_registry()

        with pytest.raises(AdapterNotFoundError) as exc_info:
            registry.get_adapter_for_file("data.xyz")

        assert exc_info.value.file_path == "data.xyz"

    def test_list_adapters_returns_all_metadata(self) -> None:
        """AC-2.2.6: list_adapters() returns all registered AdapterMetadata."""
        registry = create_default_registry()

        adapters = registry.list_adapters()

        assert len(adapters) == 4
        adapter_ids = {a.adapter_id for a in adapters}
        assert adapter_ids == {"csv", "excel", "json", "parquet"}
        assert all(isinstance(a, AdapterMetadata) for a in adapters)


class TestDefaultRegistry:
    """Test AC-2.3: Default Registry requirements."""

    def test_default_registry_has_csv_adapter(self) -> None:
        """AC-2.3.1: create_default_registry() registers CSV adapter."""
        registry = create_default_registry()

        assert "csv" in registry
        adapter = registry.get_adapter("csv")
        assert adapter.metadata.adapter_id == "csv"

    def test_default_registry_has_excel_adapter(self) -> None:
        """AC-2.3.2: create_default_registry() registers Excel adapter."""
        registry = create_default_registry()

        assert "excel" in registry
        adapter = registry.get_adapter("excel")
        assert adapter.metadata.adapter_id == "excel"

    def test_default_registry_has_json_adapter(self) -> None:
        """AC-2.3.3: create_default_registry() registers JSON adapter."""
        registry = create_default_registry()

        assert "json" in registry
        adapter = registry.get_adapter("json")
        assert adapter.metadata.adapter_id == "json"


class TestAdapterRegistryUnregister:
    """Test unregister functionality."""

    def test_unregister_removes_adapter(self) -> None:
        """Unregister removes adapter from registry."""
        registry = AdapterRegistry()
        registry.register(CSVAdapter())

        registry.unregister("csv")

        assert "csv" not in registry
        assert len(registry) == 0

    def test_unregister_removes_extension_mappings(self) -> None:
        """Unregister removes extension mappings."""
        registry = AdapterRegistry()
        registry.register(CSVAdapter())

        registry.unregister("csv")

        state = registry.get_state()
        assert ".csv" not in state.extension_map

    def test_unregister_unknown_raises_error(self) -> None:
        """Unregister unknown adapter raises AdapterNotFoundError."""
        registry = AdapterRegistry()

        with pytest.raises(AdapterNotFoundError):
            registry.unregister("unknown")


class TestAdapterRegistryState:
    """Test registry state serialization."""

    def test_get_state_returns_complete_state(self) -> None:
        """get_state returns complete registry state."""
        registry = create_default_registry()

        state = registry.get_state()

        assert len(state.adapters) == 4
        assert len(state.extension_map) > 0
        assert state.last_updated is not None

    def test_state_adapters_have_metadata(self) -> None:
        """State entries include adapter metadata."""
        registry = create_default_registry()

        state = registry.get_state()

        for entry in state.adapters:
            assert entry.adapter_id is not None
            assert entry.metadata is not None
            assert entry.registered_at is not None
