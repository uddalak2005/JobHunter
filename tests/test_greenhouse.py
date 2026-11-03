import httpx
import pytest
import respx

from ingest.adapters.base import JobFetcher
from ingest.adapters.greenhouse import GreenhouseAdapter
from ingest.schemas import ATSBoard

board = ATSBoard(
    provider="greenhouse",
    board_id="stripe",
    company_name="Stripe",
)

@pytest.mark.asyncio
async def test_fetch_jobs_success():
    
    with respx.mock(
        base_url="https://boards-api.greenhouse.io"
    ) as router :
        
        router.get("/v1/boards/stripe/jobs").mock(
            return_value = httpx.Response(
                200,
                json = {
                    "jobs": [
                        {
                            "id": 12345,
                            "title": "Software Engineer Intern",
                            "location": {
                                "name": "Bangalore"
                            },
                            "content": "<p>Backend internship</p>",
                            "absolute_url": "https://example.com/apply",
                            "first_published": "2026-10-01T10:00:00Z",
                        }
                    ]
                }
            )
        )
        
        async with httpx.AsyncClient() as client:
            
            adapter : JobFetcher = GreenhouseAdapter()
            
            jobs = await adapter.fetch_jobs(board, client)
            
            assert len(jobs) == 1
            assert jobs[0].external_id == "12345"
            assert jobs[0].title == "Software Engineer Intern"
            assert jobs[0].company == "Stripe"
            assert jobs[0].location == "Bangalore"
            assert jobs[0].source == "greenhouse"
            assert jobs[0].posted_at is not None
            assert jobs[0].discovered_at is not None
            assert router.calls.call_count == 1
            
            
@pytest.mark.asyncio
async def test_fetch_jobs_not_found():
    
    with respx.mock(
        base_url="https://boards-api.greenhouse.io"
    ) as router : 
        
        router.get("/v1/boards/stripe/jobs").mock(
            return_value = httpx.Response(404)
        )
        
        async with httpx.AsyncClient() as client:
            adapter : JobFetcher = GreenhouseAdapter()
            
            with pytest.raises(httpx.HTTPStatusError):
                await adapter.fetch_jobs(board, client)
                
@pytest.mark.asyncio
async def test_fetch_jobs_server_error():

    with respx.mock(
        base_url="https://boards-api.greenhouse.io"
    ) as router:

        router.get("/v1/boards/stripe/jobs").mock(
            return_value=httpx.Response(500)
        )

        async with httpx.AsyncClient() as client:
            adapter : JobFetcher = GreenhouseAdapter()

            with pytest.raises(httpx.HTTPStatusError):
                await adapter.fetch_jobs(board, client)
                
@pytest.mark.asyncio
async def test_fetch_jobs_empty_board():

    with respx.mock(base_url="https://boards-api.greenhouse.io") as router:
        router.get("/v1/boards/stripe/jobs").mock(
            return_value=httpx.Response(200, json={
                "jobs": []
            })
        )

        async with httpx.AsyncClient() as client:
            adapter = GreenhouseAdapter()

            jobs = await adapter.fetch_jobs(board, client)

            assert jobs == []