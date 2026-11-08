import httpx
import pytest
import respx

from ingest.adapters.base import JobFetcher
from ingest.adapters.lever import LeverAdapter
from ingest.schemas import ATSBoard

board = ATSBoard(
    provider="lever",
    board_id="stripe",
    company_name="Stripe",
)


@pytest.mark.asyncio
async def test_fetch_jobs_success():

    with respx.mock(base_url="https://api.lever.co") as router:
        router.get("/v0/postings/stripe").mock(
            return_value=httpx.Response(
                200,
                json=[
                    {
                        "id": "abc123",
                        "text": "Software Engineer Intern",
                        "categories": {"location": "Bangalore"},
                        "descriptionPlain": "Backend internship",
                        "applyUrl": "https://example.com/apply",
                        "createdAt": 1790848800000,
                    }
                ],
            )
        )

        async with httpx.AsyncClient() as client:
            adapter: JobFetcher = LeverAdapter()

            jobs = await adapter.fetch_jobs(board, client)

            assert len(jobs) == 1
            assert jobs[0].external_id == "abc123"
            assert jobs[0].title == "Software Engineer Intern"
            assert jobs[0].company == "Stripe"
            assert jobs[0].location == "Bangalore"
            assert jobs[0].source == "lever"
            assert jobs[0].posted_at is not None
            assert jobs[0].discovered_at is not None
            assert router.calls.call_count == 1


@pytest.mark.asyncio
async def test_fetch_jobs_not_found():

    with respx.mock(base_url="https://api.lever.co") as router:
        router.get("/v0/postings/stripe").mock(return_value=httpx.Response(404))

        async with httpx.AsyncClient() as client:
            adapter: JobFetcher = LeverAdapter()

            with pytest.raises(httpx.HTTPStatusError):
                await adapter.fetch_jobs(board, client)


@pytest.mark.asyncio
async def test_fetch_jobs_server_error():

    with respx.mock(base_url="https://api.lever.co") as router:
        router.get("/v0/postings/stripe").mock(return_value=httpx.Response(500))

        async with httpx.AsyncClient() as client:
            adapter: JobFetcher = LeverAdapter()

            with pytest.raises(httpx.HTTPStatusError):
                await adapter.fetch_jobs(board, client)


@pytest.mark.asyncio
async def test_fetch_jobs_empty_board():

    with respx.mock(base_url="https://api.lever.co") as router:
        router.get("/v0/postings/stripe").mock(
            return_value=httpx.Response(200, json=[])
        )

        async with httpx.AsyncClient() as client:
            adapter = LeverAdapter()

            jobs = await adapter.fetch_jobs(board, client)

            assert jobs == []
