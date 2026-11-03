
from datetime import datetime

import httpx

from ingest.adapters.base import JobFetcher
from ingest.schemas import ATSBoard, NormalizedJob


class AshbyAdapter(JobFetcher):
    BASE_URL = "https://api.ashbyhq.com/posting-api/job-board"

    async def fetch_jobs(
        self,
        board: ATSBoard,
        client: httpx.AsyncClient,
    ) -> list[NormalizedJob]:

        if board.provider != "ashby":
            raise ValueError("AshbyAdapter requires an Ashby board")

        response = await client.get(
            f"{self.BASE_URL}/{board.board_id}",
            timeout=20.0,
        )

        response.raise_for_status()

        jobs_data = response.json().get("jobs", [])
        normalized_jobs = []

        for job in jobs_data:
            published = job.get("publishedAt")

            normalized_job = NormalizedJob(
                external_id=str(job.get("id") or job["jobUrl"]),
                title=job["title"],
                company=board.company_name,
                location=job.get("location"),
                description=job.get("descriptionPlain"),
                apply_url=job.get("applyUrl"),
                source="ashby",
                posted_at=(
                    datetime.fromisoformat(
                        published.replace("Z", "+00:00")
                    )
                    if published else None
                ),
            )

            normalized_jobs.append(normalized_job)

        return normalized_jobs