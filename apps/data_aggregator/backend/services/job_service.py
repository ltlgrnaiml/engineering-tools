"""Background Job Service for DAT.

Per ADR-0040: Large File Streaming Strategy
Per SPEC-DAT-0004: Large File Streaming

This service manages background job execution for processing
large files that exceed the streaming threshold.

Features:
- In-memory job queue (production would use Redis/RabbitMQ)
- Concurrent job execution with configurable limits
- Progress tracking and cancellation
- Job timeout handling
- Retry logic for transient failures
"""

import asyncio
import secrets
from datetime import datetime, timezone
from typing import Any, Callable, Coroutine

from shared.contracts.dat.jobs import (
    BackgroundJob,
    JobListResponse,
    JobProgress,
    JobQueueStatus,
    JobResult,
    JobStatus,
    JobSubmission,
    JobType,
)


class JobNotFoundError(Exception):
    """Raised when a job is not found.

    Attributes:
        job_id: The ID of the job that was not found.
    """

    def __init__(self, job_id: str) -> None:
        """Initialize the error.

        Args:
            job_id: The ID of the job that was not found.
        """
        super().__init__(f"Job not found: {job_id}")
        self.job_id = job_id


class JobService:
    """Service for managing background jobs.

    This service provides an in-memory job queue for development.
    Production deployments should use a distributed queue like
    Redis or RabbitMQ.

    Attributes:
        max_concurrent: Maximum concurrent running jobs.
        jobs: In-memory job storage.
        running_tasks: Currently running async tasks.

    Example:
        >>> service = JobService(max_concurrent=4)
        >>> job = await service.submit_job(
        ...     JobSubmission(job_type=JobType.PARSE, file_path="data.csv")
        ... )
        >>> status = await service.get_job(job.job_id)
    """

    def __init__(self, max_concurrent: int = 4) -> None:
        """Initialize the job service.

        Args:
            max_concurrent: Maximum number of concurrent jobs.
        """
        self.max_concurrent = max_concurrent
        self.jobs: dict[str, BackgroundJob] = {}
        self.running_tasks: dict[str, asyncio.Task[None]] = {}
        self._handlers: dict[JobType, Callable[..., Coroutine[Any, Any, JobResult]]] = {}
        self._lock = asyncio.Lock()

    def _generate_job_id(self) -> str:
        """Generate a unique job ID.

        Returns:
            A unique job ID in format job_{16 hex chars}.
        """
        return f"job_{secrets.token_hex(8)}"

    def register_handler(
        self,
        job_type: JobType,
        handler: Callable[..., Coroutine[Any, Any, JobResult]],
    ) -> None:
        """Register a handler for a job type.

        Args:
            job_type: The type of job to handle.
            handler: Async function to execute the job.
        """
        self._handlers[job_type] = handler

    async def submit_job(self, submission: JobSubmission) -> BackgroundJob:
        """Submit a new job for processing.

        Args:
            submission: Job submission request.

        Returns:
            The created BackgroundJob.
        """
        job_id = self._generate_job_id()
        now = datetime.now(timezone.utc)

        job = BackgroundJob(
            job_id=job_id,
            job_type=submission.job_type,
            status=JobStatus.PENDING,
            progress=JobProgress(),
            created_at=now,
            run_id=submission.run_id,
            file_path=submission.file_path,
            options=submission.options,
            priority=submission.priority,
            timeout_seconds=submission.timeout_seconds or 3600,
        )

        async with self._lock:
            self.jobs[job_id] = job

        # Start processing if we have capacity
        await self._try_start_next_job()

        return job

    async def get_job(self, job_id: str) -> BackgroundJob:
        """Get a job by ID.

        Args:
            job_id: The job ID.

        Returns:
            The BackgroundJob.

        Raises:
            JobNotFoundError: If job not found.
        """
        job = self.jobs.get(job_id)
        if not job:
            raise JobNotFoundError(job_id)
        return job

    async def list_jobs(
        self,
        status: JobStatus | None = None,
        run_id: str | None = None,
        limit: int = 50,
        offset: int = 0,
    ) -> JobListResponse:
        """List jobs with optional filtering.

        Args:
            status: Filter by status.
            run_id: Filter by run ID.
            limit: Maximum jobs to return.
            offset: Pagination offset.

        Returns:
            JobListResponse with matching jobs.
        """
        jobs = list(self.jobs.values())

        # Apply filters
        if status:
            jobs = [j for j in jobs if j.status == status]
        if run_id:
            jobs = [j for j in jobs if j.run_id == run_id]

        # Sort by creation time (newest first)
        jobs.sort(key=lambda j: j.created_at, reverse=True)

        total = len(jobs)
        jobs = jobs[offset : offset + limit]

        return JobListResponse(
            jobs=jobs,
            total=total,
            limit=limit,
            offset=offset,
        )

    async def cancel_job(self, job_id: str) -> BackgroundJob:
        """Cancel a job.

        Args:
            job_id: The job ID.

        Returns:
            The updated job.

        Raises:
            JobNotFoundError: If job not found.
        """
        job = await self.get_job(job_id)

        if job.status in (JobStatus.COMPLETED, JobStatus.FAILED, JobStatus.CANCELLED):
            return job

        async with self._lock:
            # Cancel the running task if any
            task = self.running_tasks.get(job_id)
            if task and not task.done():
                task.cancel()
                del self.running_tasks[job_id]

            # Update job status
            job.status = JobStatus.CANCELLED
            job.completed_at = datetime.now(timezone.utc)
            self.jobs[job_id] = job

        return job

    async def delete_job(self, job_id: str) -> None:
        """Delete a job.

        Only completed, failed, or cancelled jobs can be deleted.

        Args:
            job_id: The job ID.

        Raises:
            JobNotFoundError: If job not found.
            ValueError: If job is still running.
        """
        job = await self.get_job(job_id)

        if job.status in (JobStatus.PENDING, JobStatus.RUNNING):
            raise ValueError(f"Cannot delete job in {job.status} status")

        async with self._lock:
            del self.jobs[job_id]

    async def update_progress(
        self,
        job_id: str,
        progress: JobProgress,
    ) -> BackgroundJob:
        """Update job progress.

        Args:
            job_id: The job ID.
            progress: New progress information.

        Returns:
            The updated job.

        Raises:
            JobNotFoundError: If job not found.
        """
        job = await self.get_job(job_id)

        async with self._lock:
            job.progress = progress
            self.jobs[job_id] = job

        return job

    async def get_queue_status(self) -> JobQueueStatus:
        """Get the current queue status.

        Returns:
            JobQueueStatus with queue metrics.
        """
        today = datetime.now(timezone.utc).date()

        pending = sum(1 for j in self.jobs.values() if j.status == JobStatus.PENDING)
        running = sum(1 for j in self.jobs.values() if j.status == JobStatus.RUNNING)
        completed_today = sum(
            1
            for j in self.jobs.values()
            if j.status == JobStatus.COMPLETED
            and j.completed_at
            and j.completed_at.date() == today
        )
        failed_today = sum(
            1
            for j in self.jobs.values()
            if j.status == JobStatus.FAILED
            and j.completed_at
            and j.completed_at.date() == today
        )

        return JobQueueStatus(
            pending_count=pending,
            running_count=running,
            completed_today=completed_today,
            failed_today=failed_today,
            max_concurrent=self.max_concurrent,
            queue_healthy=running <= self.max_concurrent,
        )

    async def _try_start_next_job(self) -> None:
        """Try to start the next pending job if capacity available."""
        async with self._lock:
            running_count = sum(
                1 for j in self.jobs.values() if j.status == JobStatus.RUNNING
            )

            if running_count >= self.max_concurrent:
                return

            # Find highest priority pending job
            pending_jobs = [
                j for j in self.jobs.values() if j.status == JobStatus.PENDING
            ]
            if not pending_jobs:
                return

            pending_jobs.sort(key=lambda j: (-j.priority, j.created_at))
            next_job = pending_jobs[0]

            # Start the job
            next_job.status = JobStatus.RUNNING
            next_job.started_at = datetime.now(timezone.utc)
            self.jobs[next_job.job_id] = next_job

        # Execute job in background
        task = asyncio.create_task(self._execute_job(next_job.job_id))
        self.running_tasks[next_job.job_id] = task

    async def _execute_job(self, job_id: str) -> None:
        """Execute a job.

        Args:
            job_id: The job ID to execute.
        """
        try:
            job = await self.get_job(job_id)

            # Get handler
            handler = self._handlers.get(job.job_type)
            if not handler:
                raise ValueError(f"No handler for job type: {job.job_type}")

            # Execute with timeout
            result = await asyncio.wait_for(
                handler(job),
                timeout=job.timeout_seconds,
            )

            # Update job with result
            async with self._lock:
                job.status = JobStatus.COMPLETED
                job.result = result
                job.completed_at = datetime.now(timezone.utc)
                job.progress.percentage = 100.0
                self.jobs[job_id] = job

        except asyncio.CancelledError:
            # Job was cancelled
            pass
        except asyncio.TimeoutError:
            async with self._lock:
                job = self.jobs.get(job_id)
                if job:
                    job.status = JobStatus.FAILED
                    job.error = "Job timed out"
                    job.completed_at = datetime.now(timezone.utc)
                    self.jobs[job_id] = job
        except Exception as e:
            async with self._lock:
                job = self.jobs.get(job_id)
                if job:
                    if job.retries < job.max_retries:
                        # Retry
                        job.status = JobStatus.PENDING
                        job.retries += 1
                        job.error = str(e)
                    else:
                        # Max retries exceeded
                        job.status = JobStatus.FAILED
                        job.error = str(e)
                        job.completed_at = datetime.now(timezone.utc)
                        job.result = JobResult(
                            success=False,
                            error_message=str(e),
                        )
                    self.jobs[job_id] = job
        finally:
            # Remove from running tasks
            self.running_tasks.pop(job_id, None)

            # Try to start next job
            await self._try_start_next_job()


# Global job service instance
_job_service: JobService | None = None


def get_job_service() -> JobService:
    """Get the global job service instance.

    Returns:
        The JobService singleton.
    """
    global _job_service
    if _job_service is None:
        _job_service = JobService()
    return _job_service
