"""Path Safety contracts - cross-platform path handling.

Per ADR-0018#path-safety: All public paths must be relative.
Per ADR-0013: Cross-platform compatibility for Windows, macOS, Linux.

This module defines path safety contracts and utilities.
"""

import re
from pathlib import Path

from pydantic import BaseModel, Field, field_validator

__version__ = "0.1.0"


class PathValidationError(ValueError):
    """Raised when a path violates safety rules."""

    pass


class RelativePath(BaseModel):
    """A validated relative path that is safe across all platforms.

    Per ADR-0018#path-safety:
    - No absolute paths in API responses
    - Forward slashes only (normalized)
    - No path traversal (..)
    - No leading slashes
    """

    path: str = Field(..., description="Normalized relative path with forward slashes")

    @field_validator("path", mode="before")
    @classmethod
    def validate_and_normalize(cls, v: str | Path) -> str:
        """Validate and normalize the path."""
        if isinstance(v, Path):
            v = str(v)

        # Normalize to forward slashes
        normalized = v.replace("\\", "/")

        # Check for absolute paths
        if normalized.startswith("/"):
            raise PathValidationError(f"Path must be relative, got: {v}")

        # Check for Windows absolute paths (C:/, D:/, etc.)
        if re.match(r"^[a-zA-Z]:", normalized):
            raise PathValidationError(f"Path must be relative, got absolute Windows path: {v}")

        # Check for path traversal
        if ".." in normalized.split("/"):
            raise PathValidationError(f"Path traversal (..) not allowed: {v}")

        # Remove leading ./
        while normalized.startswith("./"):
            normalized = normalized[2:]

        # Remove trailing slashes
        normalized = normalized.rstrip("/")

        return normalized

    def to_posix(self) -> str:
        """Return path with forward slashes (for storage/API)."""
        return self.path

    def to_native(self) -> Path:
        """Return path as native Path object for current OS."""
        return Path(self.path)

    def join(self, *parts: str) -> "RelativePath":
        """Join path parts safely."""
        combined = "/".join([self.path, *parts])
        return RelativePath(path=combined)


class WorkspacePath(BaseModel):
    """A path relative to the workspace root.

    Used for artifact storage paths that are relative to the workspace.
    """

    workspace_root: Path = Field(..., description="Absolute path to workspace root")
    relative_path: RelativePath = Field(..., description="Path relative to workspace")

    def absolute(self) -> Path:
        """Return the absolute path."""
        return self.workspace_root / self.relative_path.to_native()

    def exists(self) -> bool:
        """Check if the path exists."""
        return self.absolute().exists()

    @classmethod
    def from_absolute(cls, absolute_path: Path, workspace_root: Path) -> "WorkspacePath":
        """Create WorkspacePath from an absolute path within the workspace."""
        try:
            relative = absolute_path.relative_to(workspace_root)
            return cls(
                workspace_root=workspace_root,
                relative_path=RelativePath(path=str(relative)),
            )
        except ValueError as e:
            raise PathValidationError(
                f"Path {absolute_path} is not within workspace {workspace_root}"
            ) from e


class PathSafetyConfig(BaseModel):
    """Configuration for path safety validation."""

    allow_absolute_internal: bool = Field(
        default=True,
        description="Allow absolute paths in internal operations (not API responses)",
    )
    workspace_root: Path | None = Field(
        default=None,
        description="Workspace root for relative path resolution",
    )
    allowed_extensions: list[str] | None = Field(
        default=None,
        description="If set, only allow these file extensions",
    )
    blocked_patterns: list[str] = Field(
        default_factory=lambda: ["__pycache__", ".git", "node_modules", ".env"],
        description="Path patterns to block",
    )


def normalize_path(path: str | Path) -> str:
    """Normalize a path to forward slashes (cross-platform safe)."""
    return str(path).replace("\\", "/")


def is_safe_relative_path(path: str | Path) -> bool:
    """Check if a path is a safe relative path."""
    try:
        RelativePath(path=str(path))
        return True
    except (PathValidationError, ValueError):
        return False


def make_relative(path: Path, base: Path) -> RelativePath:
    """Convert an absolute path to a relative path from base.

    Raises PathValidationError if path is not under base.
    """
    try:
        relative = path.relative_to(base)
        return RelativePath(path=str(relative))
    except ValueError as e:
        raise PathValidationError(f"Path {path} is not under base {base}") from e
