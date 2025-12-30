"""Background Job System Contracts for DAT.

Per ADR-0041: Large File Streaming Strategy
Per SPEC-0027: Large File Streaming

This module defines contracts for background job processing
of large files that exceed the streaming threshold.

Features:
- Job submission and tracking
- Progress reporting with percentage
- Cancellation support
- Result storage and retrieval
- Concurrent job limits
"""

from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field

__version__ = "1.0.0"


class JobStatus(str, Enum):
    """Status of a background job."""

    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"


class JobType(str, Enum):
    """Type of background job."""

    PARSE = "parse"
    EXPORT = "export"
    VALIDATE = "validate"
    TRANSFORM = "transform"


class JobProgress(BaseModel):
    """Progress information for a job.

    Attributes:
        percentage: Completion percentage (0-100).
        current_step: Current step description.
        total_steps: Total number of steps.
        current_step_number: Current step number.
        rows_processed: Number of rows processed.
        total_rows: Total rows to process.
        bytes_processed: Bytes processed.
        total_bytes: Total bytes to process.
        eta_seconds: Estimated time to completion.
    """

    percentage: float = Field(
        0.0,
        ge=0.0,
        le=100.0,
        description="Completion percentage",
    )
    current_step: str | None = Field(
        None,
        description="Current step description",
    )
    total_steps: int | None = Field(
        None,
        ge=1,
        description="Total number of steps",
    )
    current_step_number: int | None = Field(
        None,
        ge=1,
        description="Current step number",
    )
    rows_processed: int = Field(
        0,
        ge=0,
        description="Number of rows processed",
    )
    total_rows: int | None = Field(
        None,
        ge=0,
        description="Total rows to process",
    )
    bytes_processed: int = Field(
        0,
        ge=0,
        description="Bytes processed",
    )
    total_bytes: int | None = Field(
        None,
        ge=0,
        description="Total bytes to process",
    )
    eta_seconds: float | None = Field(
        None,
        ge=0,
        description="Estimated time to completion in seconds",
    )


class JobResult(BaseModel):
    """Result of a completed job.

    Attributes:
        success: Whether job completed successfully.
        output_path: Path to output file/artifact.
        row_count: Number of rows in output.
        error_message: Error message if failed.
        warnings: Warning messages during processing.
        metadata: Additional result metadata.
    """

    success: bool = Field(..., description="Whether job completed successfully")
    output_path: str | None = Field(
        None,
        description="Relative path to output artifact",
    )
    row_count: int | None = Field(
        None,
        ge=0,
        description="Number of rows in output",
    )
    error_message: str | None = Field(
        None,
        description="Error message if failed",
    )
    warnings: list[str] = Field(
        default_factory=list,
        description="Warning messages",
    )
    metadata: dict[str, Any] = Field(
        default_factory=dict,
        description="Additional result metadata",
    )


class BackgroundJob(BaseModel):
    """Background job model.

    Represents a long-running job for processing large files.

    Attributes:
        job_id: Unique job identifier.
        job_type: Type of job.
        status: Current job status.
        progress: Progress information.
        result: Job result (when completed).
        created_at: When job was created.
        started_at: When job started processing.
        completed_at: When job finished.
        run_id: Associated DAT run ID.
        file_path: Path to input file.
        options: Job-specific options.
        priority: Job priority (higher = more urgent).
        retries: Number of retry attempts.
        max_retries: Maximum retry attempts.
        timeout_seconds: Job timeout.
        error: Last error if failed.
    """

    job_id: str = Field(
        ...,
        pattern=r"^job_[a-f0-9]{16}$",
        description="Unique job identifier",
    )
    job_type: JobType = Field(..., description="Type of job")
    status: JobStatus = Field(
        JobStatus.PENDING,
        description="Current job status",
    )
    progress: JobProgress = Field(
        default_factory=JobProgress,
        description="Progress information",
    )
    result: JobResult | None = Field(
        None,
        description="Job result when completed",
    )
    created_at: datetime = Field(..., description="When job was created")
    started_at: datetime | None = Field(
        None,
        description="When job started processing",
    )
    completed_at: datetime | None = Field(
        None,
        description="When job finished",
    )
    run_id: str | None = Field(
        None,
        description="Associated DAT run ID",
    )
    file_path: str | None = Field(
        None,
        description="Relative path to input file",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Job-specific options",
    )
    priority: int = Field(
        0,
        ge=0,
        le=100,
        description="Job priority (higher = more urgent)",
    )
    retries: int = Field(
        0,
        ge=0,
        description="Number of retry attempts",
    )
    max_retries: int = Field(
        3,
        ge=0,
        le=10,
        description="Maximum retry attempts",
    )
    timeout_seconds: int = Field(
        3600,
        ge=60,
        le=86400,
        description="Job timeout in seconds",
    )
    error: str | None = Field(
        None,
        description="Last error message if failed",
    )


class JobSubmission(BaseModel):
    """Request to submit a new job.

    Attributes:
        job_type: Type of job to run.
        run_id: Associated DAT run ID.
        file_path: Path to input file.
        options: Job-specific options.
        priority: Job priority.
        timeout_seconds: Custom timeout.
    """

    job_type: JobType = Field(..., description="Type of job to run")
    run_id: str | None = Field(
        None,
        description="Associated DAT run ID",
    )
    file_path: str | None = Field(
        None,
        description="Relative path to input file",
    )
    options: dict[str, Any] = Field(
        default_factory=dict,
        description="Job-specific options",
    )
    priority: int = Field(
        0,
        ge=0,
        le=100,
        description="Job priority",
    )
    timeout_seconds: int | None = Field(
        None,
        ge=60,
        le=86400,
        description="Custom timeout",
    )


class JobListResponse(BaseModel):
    """Response for listing jobs.

    Attributes:
        jobs: List of jobs.
        total: Total number of jobs matching query.
        limit: Maximum jobs returned.
        offset: Offset for pagination.
    """

    jobs: list[BackgroundJob] = Field(..., description="List of jobs")
    total: int = Field(..., ge=0, description="Total matching jobs")
    limit: int = Field(50, ge=1, le=100, description="Max jobs returned")
    offset: int = Field(0, ge=0, description="Pagination offset")


class JobQueueStatus(BaseModel):
    """Status of the job queue.

    Attributes:
        pending_count: Number of pending jobs.
        running_count: Number of running jobs.
        completed_today: Jobs completed today.
        failed_today: Jobs failed today.
        max_concurrent: Maximum concurrent jobs allowed.
        queue_healthy: Whether queue is healthy.
    """

    pending_count: int = Field(0, ge=0, description="Pending jobs")
    running_count: int = Field(0, ge=0, description="Running jobs")
    completed_today: int = Field(0, ge=0, description="Completed today")
    failed_today: int = Field(0, ge=0, description="Failed today")
    max_concurrent: int = Field(4, ge=1, description="Max concurrent jobs")
    queue_healthy: bool = Field(True, description="Queue health status")
