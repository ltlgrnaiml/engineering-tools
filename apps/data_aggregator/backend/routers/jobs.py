"""Background Jobs API Router for DAT.

Per ADR-0040: Large File Streaming Strategy
Per ADR-0029: API Versioning and Endpoint Naming

Provides REST endpoints for job management:
- POST /api/dat/jobs - Submit a new job
- GET /api/dat/jobs - List jobs
- GET /api/dat/jobs/{job_id} - Get job status
- DELETE /api/dat/jobs/{job_id} - Cancel/delete job
- GET /api/dat/jobs/queue/status - Get queue status
"""

from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import JSONResponse

from apps.data_aggregator.backend.services.job_service import (
    JobNotFoundError,
    get_job_service,
)
from shared.contracts.dat.jobs import (
    BackgroundJob,
    JobListResponse,
    JobQueueStatus,
    JobStatus,
    JobSubmission,
)

router = APIRouter(prefix="/jobs", tags=["jobs"])


@router.post(
    "",
    response_model=BackgroundJob,
    status_code=201,
    summary="Submit a new job",
    description="Submit a new background job for processing.",
)
async def submit_job(submission: JobSubmission) -> BackgroundJob:
    """Submit a new background job.

    Args:
        submission: Job submission request.

    Returns:
        The created BackgroundJob.
    """
    service = get_job_service()
    job = await service.submit_job(submission)
    return job


@router.get(
    "",
    response_model=JobListResponse,
    summary="List jobs",
    description="List jobs with optional filtering and pagination.",
)
async def list_jobs(
    status: JobStatus | None = Query(None, description="Filter by status"),
    run_id: str | None = Query(None, description="Filter by run ID"),
    limit: int = Query(50, ge=1, le=100, description="Max jobs to return"),
    offset: int = Query(0, ge=0, description="Pagination offset"),
) -> JobListResponse:
    """List jobs with optional filtering.

    Args:
        status: Filter by job status.
        run_id: Filter by DAT run ID.
        limit: Maximum jobs to return.
        offset: Pagination offset.

    Returns:
        JobListResponse with matching jobs.
    """
    service = get_job_service()
    return await service.list_jobs(
        status=status,
        run_id=run_id,
        limit=limit,
        offset=offset,
    )


@router.get(
    "/queue/status",
    response_model=JobQueueStatus,
    summary="Get queue status",
    description="Get current status of the job queue.",
)
async def get_queue_status() -> JobQueueStatus:
    """Get the current job queue status.

    Returns:
        JobQueueStatus with queue metrics.
    """
    service = get_job_service()
    return await service.get_queue_status()


@router.get(
    "/{job_id}",
    response_model=BackgroundJob,
    summary="Get job status",
    description="Get the current status of a specific job.",
)
async def get_job(job_id: str) -> BackgroundJob:
    """Get a job by ID.

    Args:
        job_id: The job ID.

    Returns:
        The BackgroundJob.

    Raises:
        HTTPException: If job not found.
    """
    service = get_job_service()
    try:
        return await service.get_job(job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e


@router.delete(
    "/{job_id}",
    response_model=BackgroundJob,
    summary="Cancel or delete job",
    description="Cancel a running/pending job or delete a completed job.",
)
async def cancel_or_delete_job(
    job_id: str,
    delete: bool = Query(False, description="Delete instead of cancel"),
) -> BackgroundJob | JSONResponse:
    """Cancel or delete a job.

    Args:
        job_id: The job ID.
        delete: If true, delete the job (only for completed/failed/cancelled).

    Returns:
        The updated job or success message.

    Raises:
        HTTPException: If job not found or cannot be deleted.
    """
    service = get_job_service()
    try:
        if delete:
            await service.delete_job(job_id)
            return JSONResponse(
                status_code=200,
                content={"message": f"Job {job_id} deleted"},
            )
        else:
            return await service.cancel_job(job_id)
    except JobNotFoundError as e:
        raise HTTPException(status_code=404, detail=str(e)) from e
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e
