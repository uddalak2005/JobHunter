import pytest
from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from core.models.base import Base
from core.repositories.job_repository import JobRepository, SaveResult
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
def sample_job_list():
    return [
        NormalizedJob(
            external_id="12345",
            title="Backend Engineer Intern",
            company="Stripe",
            location="Bangalore",
            description="Python backend internship",
            apply_url="https://example.com/apply",
            source="greenhouse"
        ),
        NormalizedJob(
            external_id="67890",
            title="Frontend Engineer Intern",
            company="Stripe",
            location="Bangalore",
            description="React frontend internship",
            apply_url="https://example.com/apply2",
            source="lever"
        ),
        NormalizedJob(
            external_id="54321",
            title="Data Scientist Intern",
            company="Spotify",
            location="New York",
            description="Data science internship",
            apply_url="https://example.com/apply3",
            source="ashby"
        ),
        NormalizedJob(
            external_id="128945",
            title="Backend Engineer 1",
            company="Stripe",
            location="Bangalore",
            description="Python backend internship",
            apply_url="https://example.com/apply",
            source="greenhouse"
        ),
        NormalizedJob(
            external_id="67891",
            title="Frontend Engineer 1",
            company="Stripe",
            location="Bangalore",
            description="React frontend internship",
            apply_url="https://example.com/apply2",
            source="lever"
        ),
    ]
    
@pytest.mark.asyncio
async def test_save_jobs(db_session, sample_job_list):
    repository = JobRepository(db_session)
    
    result_all_inserted: SaveResult = await repository.save_jobs(
        sample_job_list[:3]
    )
    
    assert result_all_inserted.inserted == 3
    assert result_all_inserted.skipped == 0
    
    result_duplicates: SaveResult = await repository.save_jobs(
        sample_job_list[:3]
    )
    
    assert result_duplicates.inserted == 0
    assert result_duplicates.skipped == 3
    
    result_mixed: SaveResult = await repository.save_jobs(sample_job_list[2:])
    assert result_mixed.inserted == 2
    assert result_mixed.skipped == 1


@pytest.mark.asyncio
async def test_save_jobs_checks_duplicates_in_bounded_batches(db_session):
    engine = db_session.bind.sync_engine
    job_selects = 0

    def count_job_selects(
        connection, cursor, statement, parameters, context, executemany
    ):
        nonlocal job_selects
        if (
            statement.lstrip().upper().startswith("SELECT")
            and "FROM jobs" in statement
        ):
            job_selects += 1

    event.listen(engine, "before_cursor_execute", count_job_selects)
    jobs = [
        NormalizedJob(
            external_id=f"job-{index}",
            title=f"Engineer {index}",
            company="Example Co",
            source="greenhouse",
        )
        for index in range(801)
    ]
    jobs.append(jobs[0].model_copy())

    try:
        result = await JobRepository(db_session).save_jobs(jobs)
    finally:
        event.remove(engine, "before_cursor_execute", count_job_selects)

    assert result == SaveResult(inserted=801, skipped=1)
    assert job_selects == 3
    
    
    
    