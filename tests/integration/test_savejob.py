import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker

from core.models.base import Base
from core.models.job import Job
from core.repositories.job_repository import JobRepository
from ingest.schemas import NormalizedJob


@pytest.fixture
async def db_session():
    engine = create_async_engine("sqlite+aiosqlite:///:memory:", echo=True)
    
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
        
    TestSession = async_sessionmaker(engine, expire_on_commit=False)
    
    async with TestSession() as session:
        yield session
        
    await engine.dispose()
    
@pytest.fixture
def sample_job():
    return NormalizedJob(
        external_id="12345",
        title="Backend Engineer Intern",
        company="Stripe",
        location="Bangalore",
        description="Python backend internship",
        apply_url="https://example.com/apply",
        source="greenhouse"
    )
    
@pytest.mark.asyncio
async def test_save_job(db_session, sample_job):
    
    respoitory = JobRepository(db_session)
    
    result = await respoitory.save_job(sample_job)
    
    assert result is True
    
    await db_session.flush()
    
    saved_job = await db_session.scalar(
        select(Job).where(
            Job.source == sample_job.source,
            Job.external_id == sample_job.external_id
        )
    )
    
    assert saved_job is not None
    assert saved_job.title == sample_job.title
    assert saved_job.company == sample_job.company  
    
@pytest.mark.asyncio
async def test_save_duplicate_job(db_session, sample_job):
    repository = JobRepository(db_session)

    first_result = await repository.save_job(sample_job)
    second_result = await repository.save_job(sample_job)

    assert first_result is True
    assert second_result is False

    await db_session.flush()

    saved_jobs = await db_session.scalars(
        select(Job).where(
            Job.source == "greenhouse",
            Job.external_id == "12345"
        )
    )
    assert len(saved_jobs.all()) == 1