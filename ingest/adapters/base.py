from typing import Protocol

import httpx

from ingest.schemas import NormalizedJob, ATSBoard


class JobFetcher(Protocol):

    async def fetch_jobs(self, board : ATSBoard, client: httpx.AsyncClient) -> list[NormalizedJob]:
        ...