from sqlalchemy.ext.asyncio import AsyncSession
from core.repositories.job_repository import JobRepository, SaveResult


class JobService:
    """
    Service for managing job-related operations.
    """
    
    def __init__(self, session : AsyncSession):
        self.session = session
        self.repository = JobRepository(session)
        
    async def save_jobs(self, jobs: list) -> SaveResult:
        """
        Saves a list of jobs to the database.
        
        Args:
            jobs(list): A list of job objects to be saved.
            
        Returns:
            SaveResult: An object containing the count of inserted and skipped jobs.
        """
        
        
        async with self.session.begin():
            result : SaveResult = await self.repository.save_jobs(jobs)
            
        return result