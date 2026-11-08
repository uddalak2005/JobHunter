from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.job_repository import JobRepository, SaveResult


class JobService:
    def __init__(self, session : AsyncSession):
        self.session = session
        self.repository = JobRepository(session)
        
    async def save_jobs(self, jobs: list) -> SaveResult:
        
        async with self.session.begin():
            result : SaveResult = await self.repository.save_jobs(jobs)
            
        return result