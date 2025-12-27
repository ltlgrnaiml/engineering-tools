"""DevTools contracts package.

Per ADR-0027: DevTools Page Architecture.

Exports all DevTools-related Pydantic contracts.
"""

from shared.contracts.devtools.api import (
    ADRContent,
    ADRDeleteRequest,
    ADRDeleteResponse,
    ADRListItem,
    ADRListResponse,
    ADRReadResponse,
    ADRSaveRequest,
    ADRSaveResponse,
    ADRScope,
    ADRStatus,
    ADRValidationRequest,
    ADRValidationResponse,
    APITestRequest,
    APITestResponse,
    ConfigFileInfo,
    ConfigFileListResponse,
    ConfigFileReadResponse,
    ConfigFileSaveRequest,
    ConfigFileSaveResponse,
    ConfigFileType,
    DevToolsInfo,
    DevToolsState,
    DevToolsToggleRequest,
    DevToolsToggleResponse,
    SchemaValidationRequest,
    SchemaValidationResponse,
)

__version__ = "0.1.0"

__all__ = [
    # DevTools State
    "DevToolsState",
    "DevToolsToggleRequest",
    "DevToolsToggleResponse",
    "DevToolsInfo",
    # ADR Management
    "ADRScope",
    "ADRStatus",
    "ADRListItem",
    "ADRListResponse",
    "ADRContent",
    "ADRReadResponse",
    "ADRSaveRequest",
    "ADRSaveResponse",
    "ADRDeleteRequest",
    "ADRDeleteResponse",
    "ADRValidationRequest",
    "ADRValidationResponse",
    # Config Management
    "ConfigFileType",
    "ConfigFileInfo",
    "ConfigFileListResponse",
    "ConfigFileReadResponse",
    "ConfigFileSaveRequest",
    "ConfigFileSaveResponse",
    # Utilities
    "SchemaValidationRequest",
    "SchemaValidationResponse",
    "APITestRequest",
    "APITestResponse",
]
