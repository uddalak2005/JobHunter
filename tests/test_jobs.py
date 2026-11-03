import pytest

from core.database import AsyncSessionLocal
from core.models.job import Job


@pytest.mark.asyncio
async def test_create_and_retrieve_job():
    async with AsyncSessionLocal() as session:
        job = Job(
            title="Software Engineer Intern",
            company="Google",
            location="Bangalore",
            description="Backend engineering internship",
            apply_url="https://example.com/google-intern",
            source="greenhouse",
        )

        session.add(job)

        await session.flush()  # Flush to get the ID assigned and not commit yet
        job_id = job.id

        print(f"The generated ID is: {job_id}")
        assert job.id is not None

        result = await session.get(Job, job_id)

        assert result is not None
        assert result.title == "Software Engineer Intern"
        assert result.company == "Google"
        assert result.location == "Bangalore"
        assert result.description == "Backend engineering internship"
        assert result.apply_url == "https://example.com/google-intern"
        assert result.source == "greenhouse"

        await (
            session.rollback()
        )  # Rollback to clean up after the test and close the tracsaction
