"""Tests for DevTools API contracts.

Per ADR-0027: DevTools Page Architecture.
Tests for DevTools state management and API contracts.
"""

from datetime import datetime, timezone

import pytest

from shared.contracts.devtools.api import (
    ADRContent,
    ADRListItem,
    ADRListResponse,
    ADRSaveRequest,
    ADRSaveResponse,
    ADRScope,
    ADRStatus,
    ADRValidationRequest,
    ADRValidationResponse,
    APITestRequest,
    APITestResponse,
    ConfigFileInfo,
    ConfigFileType,
    DevToolsInfo,
    DevToolsState,
    DevToolsToggleRequest,
    DevToolsToggleResponse,
    SchemaValidationRequest,
    SchemaValidationResponse,
)


class TestDevToolsState:
    """Tests for DevToolsState model."""

    def test_default_state_disabled(self) -> None:
        """DevTools should be disabled by default."""
        state = DevToolsState()

        assert state.enabled is False
        assert state.enabled_via is None
        assert state.enabled_at is None

    def test_enabled_state(self) -> None:
        """Enabled state should track how it was enabled."""
        now = datetime.now(timezone.utc)
        state = DevToolsState(
            enabled=True,
            enabled_via="url_param",
            enabled_at=now,
        )

        assert state.enabled is True
        assert state.enabled_via == "url_param"


class TestDevToolsToggle:
    """Tests for DevTools toggle request/response."""

    def test_toggle_request(self) -> None:
        """Toggle request should specify enable state and persistence."""
        request = DevToolsToggleRequest(enabled=True, persist=False)

        assert request.enabled is True
        assert request.persist is False

    def test_toggle_response(self) -> None:
        """Toggle response should include new state and message."""
        response = DevToolsToggleResponse(
            state=DevToolsState(enabled=True, enabled_via="debug_panel"),
            message="DevTools enabled via debug panel",
        )

        assert response.state.enabled is True
        assert "enabled" in response.message.lower()


class TestADRManagement:
    """Tests for ADR management contracts."""

    def test_adr_scopes(self) -> None:
        """All ADR scopes should be valid."""
        valid_scopes = [
            ADRScope.CORE,
            ADRScope.DAT,
            ADRScope.PPTX,
            ADRScope.SOV,
            ADRScope.SHARED,
            ADRScope.DEVTOOLS,
        ]

        for scope in valid_scopes:
            item = ADRListItem(
                id="ADR-0001",
                title="Test ADR",
                status=ADRStatus.ACCEPTED,
                scope=scope,
                date="2024-01-01",
                file_path=f".adrs/{scope.value}/test.json",
            )
            assert item.scope == scope

    def test_adr_statuses(self) -> None:
        """All ADR statuses should be valid."""
        statuses = [
            ADRStatus.DRAFT,
            ADRStatus.PROPOSED,
            ADRStatus.ACCEPTED,
            ADRStatus.DEPRECATED,
            ADRStatus.SUPERSEDED,
        ]

        for status in statuses:
            item = ADRListItem(
                id="ADR-0001",
                title="Test",
                status=status,
                scope=ADRScope.CORE,
                date="2024-01-01",
                file_path=".adrs/core/test.json",
            )
            assert item.status == status

    def test_adr_list_response(self) -> None:
        """ADR list response should include items and metadata."""
        items = [
            ADRListItem(
                id="ADR-0001",
                title="First ADR",
                status=ADRStatus.ACCEPTED,
                scope=ADRScope.CORE,
                date="2024-01-01",
                file_path=".adrs/core/ADR-0001.json",
            ),
            ADRListItem(
                id="ADR-0002",
                title="Second ADR",
                status=ADRStatus.PROPOSED,
                scope=ADRScope.DAT,
                date="2024-01-02",
                file_path=".adrs/dat/ADR-0002.json",
            ),
        ]

        response = ADRListResponse(
            adrs=items,
            total=2,
            scopes=[ADRScope.CORE, ADRScope.DAT],
        )

        assert response.total == 2
        assert len(response.scopes) == 2

    def test_adr_content(self) -> None:
        """ADR content should include full JSON structure."""
        content = ADRContent(
            id="ADR-0001",
            title="Test ADR",
            status=ADRStatus.ACCEPTED,
            scope=ADRScope.CORE,
            date="2024-01-01",
            content={
                "id": "ADR-0001",
                "title": "Test ADR",
                "decision_primary": "Use this approach",
                "key_constraints": ["constraint1", "constraint2"],
            },
            file_path=".adrs/core/ADR-0001.json",
        )

        assert content.content["decision_primary"] == "Use this approach"
        assert len(content.content["key_constraints"]) == 2

    def test_adr_save_request(self) -> None:
        """ADR save request should include content and options."""
        request = ADRSaveRequest(
            file_path=".adrs/core/ADR-0001.json",
            content={"id": "ADR-0001", "title": "Updated"},
            create_backup=True,
        )

        assert request.create_backup is True
        assert request.content["title"] == "Updated"

    def test_adr_save_response_success(self) -> None:
        """Successful save response should include path and backup info."""
        response = ADRSaveResponse(
            success=True,
            file_path=".adrs/core/ADR-0001.json",
            backup_path=".adrs/core/ADR-0001.json.bak",
            message="ADR saved successfully",
        )

        assert response.success is True
        assert response.backup_path is not None

    def test_adr_save_response_failure(self) -> None:
        """Failed save response should include errors."""
        response = ADRSaveResponse(
            success=False,
            file_path=".adrs/core/ADR-0001.json",
            validation_errors=["Missing required field: decision_primary"],
            message="Validation failed",
        )

        assert response.success is False
        assert len(response.validation_errors) > 0

    def test_adr_validation(self) -> None:
        """ADR validation should check content structure."""
        request = ADRValidationRequest(
            content={"id": "ADR-0001", "title": "Test"},
        )

        # Valid response
        valid_response = ADRValidationResponse(valid=True)
        assert valid_response.valid is True

        # Invalid response
        invalid_response = ADRValidationResponse(
            valid=False,
            errors=["Missing required field: status"],
            warnings=["Consider adding alternatives_considered"],
        )
        assert invalid_response.valid is False
        assert len(invalid_response.errors) > 0


class TestConfigManagement:
    """Tests for config file management contracts."""

    def test_config_file_types(self) -> None:
        """All config file types should be valid."""
        types = [
            ConfigFileType.DOMAIN_CONFIG,
            ConfigFileType.PROFILE,
            ConfigFileType.MESSAGE_CATALOG,
        ]

        for file_type in types:
            info = ConfigFileInfo(
                file_type=file_type,
                file_path=f"config/{file_type.value}.yaml",
                name=f"Test {file_type.value}",
            )
            assert info.file_type == file_type

    def test_config_file_info(self) -> None:
        """Config file info should include metadata."""
        now = datetime.now(timezone.utc)
        info = ConfigFileInfo(
            file_type=ConfigFileType.DOMAIN_CONFIG,
            file_path="apps/pptx_generator/config/domain_config.yaml",
            name="PPTX Domain Config",
            description="Domain-specific configuration for PPTX generator",
            last_modified=now,
            size_bytes=2048,
        )

        assert info.size_bytes == 2048
        assert info.last_modified == now


class TestSchemaValidation:
    """Tests for schema validation utility contracts."""

    def test_schema_validation_request(self) -> None:
        """Schema validation request should specify model and data."""
        request = SchemaValidationRequest(
            schema_name="DataSetManifest",
            data={"id": "ds_001", "name": "Test Dataset"},
        )

        assert request.schema_name == "DataSetManifest"
        assert "id" in request.data

    def test_schema_validation_success(self) -> None:
        """Successful validation should return validated data."""
        response = SchemaValidationResponse(
            valid=True,
            schema_name="DataSetManifest",
            validated_data={"id": "ds_001", "name": "Test Dataset"},
        )

        assert response.valid is True
        assert response.validated_data is not None

    def test_schema_validation_failure(self) -> None:
        """Failed validation should return errors."""
        response = SchemaValidationResponse(
            valid=False,
            schema_name="DataSetManifest",
            errors=[
                {"loc": ["id"], "msg": "field required", "type": "value_error.missing"}
            ],
        )

        assert response.valid is False
        assert len(response.errors) > 0


class TestAPITester:
    """Tests for API tester utility contracts."""

    def test_api_test_request(self) -> None:
        """API test request should include method and path."""
        request = APITestRequest(
            method="POST",
            path="/api/datasets",
            headers={"Content-Type": "application/json"},
            body={"name": "Test Dataset"},
            timeout_seconds=30.0,
        )

        assert request.method == "POST"
        assert request.path == "/api/datasets"
        assert request.body is not None

    def test_api_test_request_validation(self) -> None:
        """API test request should validate timeout bounds."""
        # Valid timeout
        APITestRequest(method="GET", path="/health", timeout_seconds=60.0)

        # Invalid timeout - too low
        with pytest.raises(ValueError):
            APITestRequest(method="GET", path="/health", timeout_seconds=0.5)

        # Invalid timeout - too high
        with pytest.raises(ValueError):
            APITestRequest(method="GET", path="/health", timeout_seconds=500.0)

    def test_api_test_response_success(self) -> None:
        """Successful API response should include body and timing."""
        response = APITestResponse(
            success=True,
            status_code=200,
            headers={"content-type": "application/json"},
            body={"status": "ok"},
            duration_ms=45.5,
        )

        assert response.success is True
        assert response.status_code == 200
        assert response.duration_ms > 0

    def test_api_test_response_error(self) -> None:
        """Failed API response should include error details."""
        response = APITestResponse(
            success=False,
            status_code=500,
            headers={},
            body=None,
            duration_ms=100.0,
            error="Connection timeout",
        )

        assert response.success is False
        assert response.error is not None


class TestDevToolsInfo:
    """Tests for DevToolsInfo model."""

    def test_devtools_info_defaults(self) -> None:
        """DevToolsInfo should have default utilities."""
        info = DevToolsInfo()

        assert info.version is not None
        assert "adr_reader_editor" in info.utilities
        assert "api_tester" in info.utilities

    def test_devtools_info_with_counts(self) -> None:
        """DevToolsInfo should include ADR and config counts."""
        info = DevToolsInfo(
            adr_count=29,
            config_count=5,
            schemas_available=["DataSetManifest", "Pipeline", "ChartSpec"],
        )

        assert info.adr_count == 29
        assert info.config_count == 5
        assert len(info.schemas_available) == 3
