from dataclasses import dataclass

from sqlalchemy import select, tuple_
from sqlalchemy.ext.asyncio import AsyncSession

from core.models.job import Job
from ingest.schemas import NormalizedJob

EXISTING_JOB_QUERY_CHUNK_SIZE = 400

@dataclass
class SaveResult:
    inserted: int
    skipped: int

class JobRepository:
    
    def __init__(self, session: AsyncSession):
        self.session = session
        
    async def save_job(self, job: NormalizedJob) -> bool:
        
        existing_job = await self.session.scalar(
        select(Job).where(
                Job.source == job.source,
                Job.external_id == job.external_id
            )
        )

        if existing_job:
            return False
        
        new_job : Job = Job(
            title=job.title,
            company=job.company,
            location=job.location,
            description=job.description,
            apply_url=job.apply_url,
            source=job.source,
            posted_at=job.posted_at,
            discovered_at=job.discovered_at,
            external_id=job.external_id
        )
        
        self.session.add(new_job)
        return True
    
    async def save_jobs(self, jobs: list[NormalizedJob]) -> SaveResult:
        if not jobs:
            return SaveResult(inserted=0, skipped=0)

        job_keys = list(dict.fromkeys((job.source, job.external_id) for job in jobs))
        existing_keys: set[tuple[str, str]] = set()

        for offset in range(0, len(job_keys), EXISTING_JOB_QUERY_CHUNK_SIZE):
            key_chunk = job_keys[offset : offset + EXISTING_JOB_QUERY_CHUNK_SIZE]
            existing_result = await self.session.execute(
                select(Job.source, Job.external_id).where(
                    tuple_(Job.source, Job.external_id).in_(key_chunk)
                )
            )
            existing_keys.update(existing_result.tuples().all())

        seen_keys: set[tuple[str, str]] = set()
        new_jobs: list[Job] = []
        skipped = 0

        for job in jobs:
            job_key = (job.source, job.external_id)
            if job_key in existing_keys or job_key in seen_keys:
                skipped += 1
                continue

            seen_keys.add(job_key)
            new_jobs.append(
                Job(
                    title=job.title,
                    company=job.company,
                    location=job.location,
                    description=job.description,
                    apply_url=job.apply_url,
                    source=job.source,
                    posted_at=job.posted_at,
                    discovered_at=job.discovered_at,
                    external_id=job.external_id,
                )
            )

        self.session.add_all(new_jobs)
        return SaveResult(inserted=len(new_jobs), skipped=skipped)