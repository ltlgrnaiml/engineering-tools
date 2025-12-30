"""Unit tests for Background Job Service.

Per SPEC-0027: Large File Streaming
Tests P3-2: Background Job System requirements.
"""

import pytest

from apps.data_aggregator.backend.services.job_service import (
    JobNotFoundError,
    JobService,
)
from shared.contracts.dat.jobs import (
    BackgroundJob,
    JobProgress,
    JobResult,
    JobStatus,
    JobSubmission,
    JobType,
)


class TestJobServiceSubmission:
    """Test job submission requirements."""

    @pytest.mark.asyncio
    async def test_submit_job_returns_background_job(self) -> None:
        """P3-2.2: Submit returns BackgroundJob with status tracking."""
        service = JobService(max_concurrent=0)  # Disable auto-start for test
        submission = JobSubmission(
            job_type=JobType.PARSE,
            file_path="test.csv",
        )

        job = await service.submit_job(submission)

        assert isinstance(job, BackgroundJob)
        assert job.job_id.startswith("job_")
        assert job.job_type == JobType.PARSE
        assert job.status == JobStatus.PENDING
        assert job.file_path == "test.csv"

    @pytest.mark.asyncio
    async def test_submit_job_generates_unique_id(self) -> None:
        """Job IDs are unique."""
        service = JobService()
        submission = JobSubmission(job_type=JobType.PARSE)

        job1 = await service.submit_job(submission)
        job2 = await service.submit_job(submission)

        assert job1.job_id != job2.job_id

    @pytest.mark.asyncio
    async def test_submit_job_respects_priority(self) -> None:
        """Jobs store priority for queue ordering."""
        service = JobService(max_concurrent=0)  # Disable auto-start
        submission = JobSubmission(
            job_type=JobType.PARSE,
            priority=50,
        )

        job = await service.submit_job(submission)

        assert job.priority == 50


class TestJobServiceStatus:
    """Test job status endpoint requirements."""

    @pytest.mark.asyncio
    async def test_get_job_returns_job(self) -> None:
        """P3-2.4: GET /jobs/{job_id} returns job status."""
        service = JobService()
        submission = JobSubmission(job_type=JobType.PARSE)
        created = await service.submit_job(submission)

        job = await service.get_job(created.job_id)

        assert job.job_id == created.job_id
        assert job.status in JobStatus

    @pytest.mark.asyncio
    async def test_get_job_not_found_raises(self) -> None:
        """GET raises JobNotFoundError for unknown ID."""
        service = JobService()

        with pytest.raises(JobNotFoundError) as exc_info:
            await service.get_job("job_nonexistent12345")

        assert exc_info.value.job_id == "job_nonexistent12345"


class TestJobServiceCancellation:
    """Test job cancellation requirements."""

    @pytest.mark.asyncio
    async def test_cancel_job_updates_status(self) -> None:
        """P3-2.5: DELETE /jobs/{job_id} cancels job."""
        service = JobService(max_concurrent=0)  # Prevent auto-start
        submission = JobSubmission(job_type=JobType.PARSE)
        created = await service.submit_job(submission)

        cancelled = await service.cancel_job(created.job_id)

        assert cancelled.status == JobStatus.CANCELLED
        assert cancelled.completed_at is not None

    @pytest.mark.asyncio
    async def test_cancel_completed_job_is_noop(self) -> None:
        """Cancelling completed job returns unchanged."""
        service = JobService(max_concurrent=0)
        submission = JobSubmission(job_type=JobType.PARSE)
        job = await service.submit_job(submission)

        # Manually mark as completed
        job.status = JobStatus.COMPLETED
        service.jobs[job.job_id] = job

        result = await service.cancel_job(job.job_id)

        assert result.status == JobStatus.COMPLETED


class TestJobServiceProgress:
    """Test progress tracking requirements."""

    @pytest.mark.asyncio
    async def test_update_progress(self) -> None:
        """P3-2.6: Progress tracking with percentage."""
        service = JobService(max_concurrent=0)
        submission = JobSubmission(job_type=JobType.PARSE)
        job = await service.submit_job(submission)

        progress = JobProgress(
            percentage=50.0,
            current_step="Processing rows",
            rows_processed=5000,
            total_rows=10000,
        )

        updated = await service.update_progress(job.job_id, progress)

        assert updated.progress.percentage == 50.0
        assert updated.progress.rows_processed == 5000


class TestJobServiceListing:
    """Test job listing requirements."""

    @pytest.mark.asyncio
    async def test_list_jobs_returns_all(self) -> None:
        """P3-2.3: POST /jobs submission endpoint works."""
        service = JobService(max_concurrent=0)

        await service.submit_job(JobSubmission(job_type=JobType.PARSE))
        await service.submit_job(JobSubmission(job_type=JobType.EXPORT))

        result = await service.list_jobs()

        assert len(result.jobs) == 2
        assert result.total == 2

    @pytest.mark.asyncio
    async def test_list_jobs_filters_by_status(self) -> None:
        """List filters by status."""
        service = JobService(max_concurrent=0)
        job1 = await service.submit_job(JobSubmission(job_type=JobType.PARSE))
        await service.submit_job(JobSubmission(job_type=JobType.EXPORT))

        # Cancel first job
        await service.cancel_job(job1.job_id)

        pending = await service.list_jobs(status=JobStatus.PENDING)
        cancelled = await service.list_jobs(status=JobStatus.CANCELLED)

        assert pending.total == 1
        assert cancelled.total == 1

    @pytest.mark.asyncio
    async def test_list_jobs_pagination(self) -> None:
        """List supports pagination."""
        service = JobService(max_concurrent=0)

        for _ in range(5):
            await service.submit_job(JobSubmission(job_type=JobType.PARSE))

        page1 = await service.list_jobs(limit=2, offset=0)
        page2 = await service.list_jobs(limit=2, offset=2)

        assert len(page1.jobs) == 2
        assert len(page2.jobs) == 2
        assert page1.jobs[0].job_id != page2.jobs[0].job_id


class TestJobServiceQueue:
    """Test queue status requirements."""

    @pytest.mark.asyncio
    async def test_queue_status(self) -> None:
        """P3-2.9: Concurrent job limit configuration."""
        service = JobService(max_concurrent=4)

        await service.submit_job(JobSubmission(job_type=JobType.PARSE))
        await service.submit_job(JobSubmission(job_type=JobType.PARSE))

        status = await service.get_queue_status()

        assert status.max_concurrent == 4
        assert status.pending_count >= 0
        assert status.queue_healthy is True


class TestJobServiceDeletion:
    """Test job deletion requirements."""

    @pytest.mark.asyncio
    async def test_delete_completed_job(self) -> None:
        """Can delete completed job."""
        service = JobService(max_concurrent=0)
        job = await service.submit_job(JobSubmission(job_type=JobType.PARSE))

        # Mark as completed
        job.status = JobStatus.COMPLETED
        service.jobs[job.job_id] = job

        await service.delete_job(job.job_id)

        with pytest.raises(JobNotFoundError):
            await service.get_job(job.job_id)

    @pytest.mark.asyncio
    async def test_cannot_delete_running_job(self) -> None:
        """Cannot delete running job."""
        service = JobService(max_concurrent=0)
        job = await service.submit_job(JobSubmission(job_type=JobType.PARSE))

        # Mark as running
        job.status = JobStatus.RUNNING
        service.jobs[job.job_id] = job

        with pytest.raises(ValueError, match="Cannot delete"):
            await service.delete_job(job.job_id)
