from datetime import datetime, timezone

import httpx

from ingest.adapters.base import JobFetcher
from ingest.schemas import ATSBoard, NormalizedJob


class LeverAdapter(JobFetcher):
    BASE_URL = "https://api.lever.co/v0/postings"

    async def fetch_jobs(
        self,
        board: ATSBoard,
        client: httpx.AsyncClient,
    ) -> list[NormalizedJob]:

        if board.provider != "lever":
            raise ValueError("LeverAdapter requires a Lever board")

        response = await client.get(
            f"{self.BASE_URL}/{board.board_id}",
            params={"mode": "json"},
            timeout=20.0,
        )

        response.raise_for_status()

        jobs_data = response.json()
        normalized_jobs = []

        for job in jobs_data:
            categories = job.get("categories") or {}
            created_at = job.get("createdAt")

            normalized_job = NormalizedJob(
                external_id=str(job["id"]),
                title=job["text"],
                company=board.company_name,
                location=categories.get("location"),
                description=(job.get("descriptionPlain") or job.get("description")),
                apply_url=job.get("applyUrl"),
                source="lever",
                posted_at=(
                    datetime.fromtimestamp(
                        created_at / 1000,
                        tz=timezone.utc,
                    )
                    if created_at is not None
                    else None
                ),
            )

            normalized_jobs.append(normalized_job)

        return normalized_jobs
