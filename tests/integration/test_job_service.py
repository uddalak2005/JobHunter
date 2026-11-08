import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.models import job
from core.repositories.job_repository import SaveResult
from ingest.schemas import NormalizedJob
from core.models.base import Base
from core.models.job import Job
from core.services.job_service import JobService


@pytest.fixture
async def db_session() :
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSession = async_sessionmaker(engine, expire_on_commit=False)
    
    async with TestSession() as session:
        yield session
        
    await engine.dispose()
    
@pytest.fixture
def sample_jobs():
    return [
        NormalizedJob(
            external_id=str(i),
            title=f"Backend Intern {i}",
            company="Stripe",
            source="greenhouse"
        )
        for i in range(1, 4)
    ]
    
    
@pytest.mark.asyncio
async def test_save_jobs_success(db_session, sample_jobs):
    job_service = JobService(db_session)
    result = await job_service.save_jobs(sample_jobs)
    
    assert result == SaveResult(inserted = 3, skipped = 0)
    
    saved_jobs = await db_session.scalars(select(Job))
    assert len(saved_jobs.all()) == 3
    
    
@pytest.mark.asyncio
async def test_save_jobs_failure(db_session, sample_jobs):
    service = JobService(db_session)
    
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

        raise RuntimeError("Simulated database failure")
    
    service.repository.save_jobs = failing_save_jobs
    
    with pytest.raises(RuntimeError, match = "Simulated database failure"):
        await service.save_jobs(sample_jobs)
        
    saved_jobs = await db_session.scalars(select(Job))
    
    assert len(saved_jobs.all()) == 0