from datetime import datetime

import httpx

from ingest.schemas import NormalizedJob, ATSBoard

from ingest.adapters.base import JobFetcher


class GreenhouseAdapter(JobFetcher):
    BASE_URL = "https://boards-api.greenhouse.io/v1/boards"

    async def fetch_jobs(
        self, board: ATSBoard, client: httpx.AsyncClient
    ) -> list[NormalizedJob]:

        if board.provider != "greenhouse":
            raise ValueError("GreenhouseAdapter requires a Greenhouse board")

        response = await client.get(
            f"{self.BASE_URL}/{board.board_id}/jobs",
            params={"content": "true"},
            timeout=20.0,
        )

        response.raise_for_status()

        jobs_data = response.json().get("jobs", [])
        normalized_jobs = []

        for job in jobs_data:
            location = job.get("location") or {}
            published = job.get("first_published")

            normalized_job = NormalizedJob(
                external_id=str(job["id"]),
                title=job["title"],
                company=board.company_name,
                location=location.get("name"),
                description=job.get("content"),
                apply_url=job.get("absolute_url"),
                source="greenhouse",
                posted_at=(
                    datetime.fromisoformat(published.replace("Z", "+00:00"))
                    if published
                    else None
                ),
            )

            normalized_jobs.append(normalized_job)

        return normalized_jobs
