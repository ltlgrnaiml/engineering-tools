"""Cross-Platform Concurrency contracts.

Per ADR-0012: Unified async, threading, and process parallelism for all OS.
- Tier 1: asyncio for I/O-bound async operations
- Tier 2: ThreadPoolExecutor for concurrent I/O
- Tier 3: ProcessPoolExecutor with spawn start method

This module defines contracts for concurrency configuration and platform info.
"""

import os
import platform
import shutil
import sys
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field

__version__ = "0.1.0"


class OSType(str, Enum):
    """Supported operating systems."""

    WINDOWS = "windows"
    MACOS = "macos"
    LINUX = "linux"
    UNKNOWN = "unknown"


class ShellType(str, Enum):
    """Available shell types."""

    POWERSHELL = "powershell"
    PWSH = "pwsh"  # PowerShell Core
    CMD = "cmd"
    BASH = "bash"
    ZSH = "zsh"
    SH = "sh"
    UNKNOWN = "unknown"


class ConcurrencyTier(str, Enum):
    """Concurrency execution tiers per ADR-0012."""

    ASYNC = "async"  # Tier 1: asyncio
    THREADS = "threads"  # Tier 2: ThreadPoolExecutor
    PROCESSES = "processes"  # Tier 3: ProcessPoolExecutor


class PlatformInfo(BaseModel):
    """Platform information for cross-platform operations.

    Auto-detected at runtime to configure appropriate backends.
    """

    os_type: OSType
    os_version: str
    python_version: str
    cpu_count: int
    default_shell: ShellType
    available_shells: list[ShellType]

    # Concurrency capabilities
    supports_fork: bool = Field(
        description="True on Unix, False on Windows"
    )
    recommended_start_method: Literal["spawn", "fork", "forkserver"] = Field(
        default="spawn",
        description="Per ADR-0012: Always use spawn for consistency",
    )

    @classmethod
    def detect(cls) -> "PlatformInfo":
        """Detect current platform information."""
        # Detect OS
        system = platform.system().lower()
        if system == "windows":
            os_type = OSType.WINDOWS
        elif system == "darwin":
            os_type = OSType.MACOS
        elif system == "linux":
            os_type = OSType.LINUX
        else:
            os_type = OSType.UNKNOWN

        # Detect available shells
        available_shells = []
        shell_checks = [
            (ShellType.PWSH, "pwsh"),
            (ShellType.POWERSHELL, "powershell"),
            (ShellType.BASH, "bash"),
            (ShellType.ZSH, "zsh"),
            (ShellType.SH, "sh"),
        ]
        for shell_type, cmd in shell_checks:
            if shutil.which(cmd):
                available_shells.append(shell_type)

        # Windows CMD
        if os_type == OSType.WINDOWS and os.environ.get("COMSPEC"):
            available_shells.append(ShellType.CMD)

        # Detect default shell
        if os_type == OSType.WINDOWS:
            if ShellType.PWSH in available_shells:
                default_shell = ShellType.PWSH
            elif ShellType.POWERSHELL in available_shells:
                default_shell = ShellType.POWERSHELL
            else:
                default_shell = ShellType.CMD
        else:
            shell_env = os.environ.get("SHELL", "")
            if "zsh" in shell_env:
                default_shell = ShellType.ZSH
            elif "bash" in shell_env:
                default_shell = ShellType.BASH
            else:
                default_shell = ShellType.SH if ShellType.SH in available_shells else ShellType.UNKNOWN

        return cls(
            os_type=os_type,
            os_version=platform.version(),
            python_version=platform.python_version(),
            cpu_count=os.cpu_count() or 1,
            default_shell=default_shell,
            available_shells=available_shells,
            supports_fork=os_type != OSType.WINDOWS,
            recommended_start_method="spawn",  # Per ADR-0012
        )


class ConcurrencyConfig(BaseModel):
    """Configuration for concurrency operations.

    Per ADR-0012: Configurable caps with sensible defaults.
    """

    max_threads: int = Field(
        default_factory=lambda: (os.cpu_count() or 1) * 4,
        ge=1,
        description="Max threads for ThreadPoolExecutor (default: 4x CPU)",
    )
    max_processes: int = Field(
        default_factory=lambda: os.cpu_count() or 1,
        ge=1,
        description="Max processes for ProcessPoolExecutor (default: CPU count)",
    )
    default_seed: int = Field(
        default=42,
        description="Default seed for deterministic operations (per ADR-0004)",
    )
    process_start_method: Literal["spawn"] = Field(
        default="spawn",
        description="Per ADR-0012: Always spawn for cross-platform consistency",
    )
    timeout_seconds: float = Field(
        default=300.0,
        ge=0,
        description="Default timeout for concurrent operations (5 minutes)",
    )

    @classmethod
    def from_env(cls) -> "ConcurrencyConfig":
        """Create config from environment variables."""
        return cls(
            max_threads=int(os.environ.get("ET_MAX_THREADS", (os.cpu_count() or 1) * 4)),
            max_processes=int(os.environ.get("ET_MAX_PROCESSES", os.cpu_count() or 1)),
            default_seed=int(os.environ.get("ET_SEED", 42)),
            timeout_seconds=float(os.environ.get("ET_TIMEOUT", 300.0)),
        )


class TaskResult(BaseModel):
    """Result of a concurrent task execution."""

    success: bool
    result: object | None = None
    error: str | None = None
    duration_ms: float = Field(ge=0)
    task_index: int = Field(ge=0)


class BatchResult(BaseModel):
    """Result of a batch concurrent operation."""

    total_tasks: int
    completed: int
    failed: int
    results: list[TaskResult]
    total_duration_ms: float


# Singleton platform info (cached at module load)
_platform_info: PlatformInfo | None = None


def get_platform_info() -> PlatformInfo:
    """Get cached platform information."""
    global _platform_info
    if _platform_info is None:
        _platform_info = PlatformInfo.detect()
    return _platform_info
