from unittest.mock import AsyncMock

import httpx
import pytest
import pytest_asyncio
import respx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.models.base import Base
from core.models.job import Job
from core.repositories.job_repository import SaveResult
from core.services.job_service import JobService
from core.services.pipeline_service import PipelineService
from ingest.discovery.registry import load_company_registry
from ingest.orchestrator import IngestionService
from ingest.schemas import ATSBoard, NormalizedJob
from main import run_ingestion


@pytest_asyncio.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:")

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    TestSession = async_sessionmaker(
        bind=engine,
        expire_on_commit=False
    )

    async with TestSession() as session:
        yield session

    await engine.dispose()


@pytest.fixture
def sample_jobs():
    return [
        NormalizedJob(
            external_id=str(i),
            title=f"Backend Engineer {i}",
            company="Stripe",
            location="Bangalore",
            source="greenhouse"
        )
        for i in range(1, 4)
    ]


@pytest.fixture
def sample_boards():
    return [
        ATSBoard(
            provider="greenhouse",
            board_id="stripe",
            company_name="Stripe"
        )
    ]
    
@pytest.mark.asyncio
async def test_pipeline_success(db_session, sample_jobs, sample_boards):

    ingestion_service = AsyncMock(spec=IngestionService)
    ingestion_service.ingest.return_value = sample_jobs

    job_service = JobService(db_session)

    pipeline = PipelineService(
        job_service=job_service,
        ingestion_service=ingestion_service
    )

    result = await pipeline.run_pipeline(sample_boards, AsyncMock())

    assert result == SaveResult(inserted=3, skipped=0)

    saved_jobs = await db_session.scalars(select(Job))
    assert len(saved_jobs.all()) == 3

    ingestion_service.ingest.assert_awaited_once_with(
        sample_boards,
        ingestion_service.ingest.call_args.args[1]
    )
    
@pytest.mark.asyncio
async def test_pipeline_no_jobs(db_session, sample_boards):

    ingestion_service = AsyncMock(spec=IngestionService)
    ingestion_service.ingest.return_value = []

    job_service = JobService(db_session)

    pipeline = PipelineService(job_service, ingestion_service)

    result = await pipeline.run_pipeline(sample_boards, AsyncMock())

    assert result == SaveResult(inserted=0, skipped=0)

    saved_jobs = await db_session.scalars(select(Job))
    assert len(saved_jobs.all()) == 0
    
@pytest.mark.asyncio
async def test_pipeline_rollback(db_session, sample_jobs, sample_boards):

    ingestion_service = AsyncMock(spec=IngestionService)
    ingestion_service.ingest.return_value = sample_jobs

    job_service = JobService(db_session)

    async def failing_save_jobs(jobs):
        job = jobs[0]

        db_session.add(
            Job(
                external_id=job.external_id,
                title=job.title,
                company=job.company,
                source=job.source
            )
        )

        await db_session.flush()

        raise RuntimeError("Database failure")

    job_service.repository.save_jobs = failing_save_jobs

    pipeline = PipelineService(job_service, ingestion_service)

    with pytest.raises(RuntimeError, match="Database failure"):
        await pipeline.run_pipeline(sample_boards, AsyncMock())

    saved_jobs = await db_session.scalars(select(Job))

    assert len(saved_jobs.all()) == 0


@pytest.mark.asyncio
async def test_default_registry_ingests_all_boards_and_deduplicates(db_session):
    session_factory = async_sessionmaker(
        bind=db_session.bind,
        expire_on_commit=False,
    )
    assert len(load_company_registry()) == 3

    with respx.mock(assert_all_called=True) as router:
        greenhouse_route = router.get(
            "https://boards-api.greenhouse.io/v1/boards/stripe/jobs",
            params={"content": "true"},
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "id": 101,
                            "title": "Software Engineer",
                            "location": {"name": "Remote"},
                            "content": "Build payments infrastructure.",
                            "absolute_url": "https://stripe.com/jobs/101",
                            "first_published": "2026-10-01T10:00:00Z",
                        }
                    ]
                },
            )
        )
        lever_route = router.get(
            "https://api.lever.co/v0/postings/spotify",
            params={"mode": "json"},
        ).mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "lever-202",
                        "text": "Backend Engineer",
                        "categories": {"location": "Remote"},
                        "createdAt": 1790848800000,
                        "descriptionPlain": "Build streaming services.",
                        "applyUrl": "https://jobs.lever.co/spotify/lever-202",
                    }
                ],
            )
        )
        ashby_route = router.get(
            "https://api.ashbyhq.com/posting-api/job-board/linear"
        ).mock(
            return_value=httpx.Response(
                200,
                json={
                    "jobs": [
                        {
                            "id": "ashby-303",
                            "title": "Product Engineer",
                            "location": "Remote",
                            "publishedAt": "2026-10-02T10:00:00Z",
                            "descriptionPlain": "Build product workflows.",
                            "applyUrl": "https://jobs.ashbyhq.com/linear/ashby-303",
                        }
                    ]
                },
            )
        )

        first_result = await run_ingestion(session_factory)
        second_result = await run_ingestion(session_factory)

    assert first_result == SaveResult(inserted=3, skipped=0)
    assert second_result == SaveResult(inserted=0, skipped=3)
    assert greenhouse_route.call_count == 2
    assert lever_route.call_count == 2
    assert ashby_route.call_count == 2

    saved_jobs = await db_session.scalars(select(Job))
    assert len(saved_jobs.all()) == 3