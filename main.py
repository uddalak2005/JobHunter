import asyncio
import logging

import httpx
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker

from core.database import AsyncSessionLocal
from core.repositories.job_repository import SaveResult
from core.services.job_service import JobService
from core.services.pipeline_service import PipelineService
from ingest.adapters.registry import AdapterRegistry
from ingest.discovery.registry import load_company_registry
from ingest.orchestrator import IngestionService


async def run_ingestion(
    session_factory: async_sessionmaker[AsyncSession],
) -> SaveResult:
    boards = load_company_registry()
    ingestion_service = IngestionService(AdapterRegistry())

    async with httpx.AsyncClient() as client:
        async with session_factory() as session:
            pipeline = PipelineService(
                job_service=JobService(session),
                ingestion_service=ingestion_service,
            )
            return await pipeline.run_pipeline(boards, client)


def main() -> None:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    print("Starting ingestion from the configured ATS boards...", flush=True)

    result = asyncio.run(run_ingestion(AsyncSessionLocal))
    print(
        "Ingestion complete: "
        f"{result.inserted} inserted, {result.skipped} already present.",
        flush=True,
    )



if __name__ == "__main__":
    main()