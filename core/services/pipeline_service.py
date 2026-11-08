import logging

import httpx

from core.repositories.job_repository import SaveResult
from core.services.job_service import JobService
from ingest.orchestrator import IngestionService
from ingest.schemas import ATSBoard

logger = logging.getLogger(__name__)


class PipelineService:
    def __init__(self, job_service : JobService, ingestion_service : IngestionService):
        self.job_service = job_service
        self.ingestion_service = ingestion_service
        
    async def run_pipeline(
        self, boards: list[ATSBoard], client: httpx.AsyncClient
    ) -> SaveResult:

        logger.info("Fetching jobs from %d ATS boards", len(boards))
        jobs = await self.ingestion_service.ingest(boards, client)
        logger.info("Fetched %d jobs; saving to the database", len(jobs))
        result : SaveResult = await self.job_service.save_jobs(jobs)
        logger.info(
            "Persistence complete: %d inserted, %d skipped",
            result.inserted,
            result.skipped,
        )
        return result
    