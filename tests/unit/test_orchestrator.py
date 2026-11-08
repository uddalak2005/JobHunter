import httpx
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime

from ingest.orchestrator import IngestionService
from ingest.schemas import ATSBoard, NormalizedJob

import pytest


@pytest.mark.asyncio
async def test_ingest_multiple_boards():
    boards = [
        ATSBoard(
            provider="greenhouse",
            board_id="stripe",
            company_name="Stripe",
        ),
        ATSBoard(
            provider="lever",
            board_id="spotify",
            company_name="Spotify",
        ),
        ATSBoard(
            provider="ashby",
            board_id="linear",
            company_name="Linear",
        ),
    ]

    jobs = [
        NormalizedJob(
            external_id="12345",
            title="Software Engineer Intern",
            company="Stripe",
            location="Bangalore",
            source="greenhouse",
            posted_at=datetime.fromisoformat("2026-10-01T10:00:00Z"),
            discovered_at=datetime.fromisoformat("2026-10-01T10:00:00Z"),
        ),
        NormalizedJob(
            external_id="67890",
            title="Data Scientist",
            company="Spotify",
            location="New York",
            source="lever",
            posted_at=datetime.fromisoformat("2026-10-02T10:00:00Z"),
            discovered_at=datetime.fromisoformat("2026-10-02T10:00:00Z"),
        ),
        NormalizedJob(
            external_id="54321",
            title="Product Manager",
            company="Linear",
            location="San Francisco",
            source="ashby",
            posted_at=datetime.fromisoformat("2026-10-03T10:00:00Z"),
            discovered_at=datetime.fromisoformat("2026-10-03T10:00:00Z"),
        ),
    ]

    greenhouse_adapter_mock = MagicMock()

    greenhouse_adapter_mock.fetch_jobs = AsyncMock(return_value=[jobs[0]])
    ### This means whenever the orchestrator calls:
    ### await greenhouse_adapter.fetch_jobs(board, client)
    ### It receives greenhouse_jobs without making an HTTP request.

    lever_adapter_mock = MagicMock()
    lever_adapter_mock.fetch_jobs = AsyncMock(return_value=[jobs[1]])

    ashby_adapter_mock = MagicMock()
    ashby_adapter_mock.fetch_jobs = AsyncMock(return_value=[jobs[2]])

    registry = MagicMock()

    ### Understand this carefully:
    ### - get_adapter("greenhouse") returns greenhouse_adapter.
    ### - get_adapter("lever") returns lever_adapter.
    ### - get_adapter("ashby") returns ashby_adapter.
    ### side_effect lets us define dynamic behaviour for a mock.

    registry.get_adapter.side_effect = {
        "greenhouse": greenhouse_adapter_mock,
        "lever": lever_adapter_mock,
        "ashby": ashby_adapter_mock,
    }.get

    service = IngestionService(registry=registry)

    async with httpx.AsyncClient() as client:
        jobs = await service.ingest(boards, client)

    assert len(jobs) == 3
    assert jobs[0].company == "Stripe"
    assert jobs[1].company == "Spotify"
    assert jobs[2].company == "Linear"

    registry.get_adapter.assert_any_call("greenhouse")
    registry.get_adapter.assert_any_call("lever")
    registry.get_adapter.assert_any_call("ashby")

    greenhouse_adapter_mock.fetch_jobs.assert_awaited_once()
    lever_adapter_mock.fetch_jobs.assert_awaited_once()
    ashby_adapter_mock.fetch_jobs.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_empty_job_board():
    greenhouse_adapter_mock = MagicMock()
    greenhouse_adapter_mock.fetch_jobs = AsyncMock(return_value=[])

    lever_adapter_mock = MagicMock()
    lever_adapter_mock.fetch_jobs = AsyncMock(return_value=[])

    ashby_adapter_mock = MagicMock()
    ashby_adapter_mock.fetch_jobs = AsyncMock(return_value=[])

    registry = MagicMock()
    registry.get_adapter.side_effect = {
        "greenhouse": greenhouse_adapter_mock,
        "lever": lever_adapter_mock,
        "ashby": ashby_adapter_mock,
    }.get

    service = IngestionService(registry)

    boards = [
        ATSBoard(
            provider="greenhouse",
            board_id="empty-company",
            company_name="Empty Company",
        ),
        ATSBoard(
            provider="lever",
            board_id="empty-company",
            company_name="Empty Company",
        ),
        ATSBoard(
            provider="ashby",
            board_id="empty-company",
            company_name="Empty Company",
        ),
    ]

    async with httpx.AsyncClient() as client:
        jobs = await service.ingest(boards, client)

    assert jobs == []
    registry.get_adapter.assert_any_call("greenhouse")
    registry.get_adapter.assert_any_call("lever")
    registry.get_adapter.assert_any_call("ashby")

    greenhouse_adapter_mock.fetch_jobs.assert_awaited_once()
    lever_adapter_mock.fetch_jobs.assert_awaited_once()
    ashby_adapter_mock.fetch_jobs.assert_awaited_once()


@pytest.mark.asyncio
async def test_ingest_unsupported_provider():
    registry = MagicMock()
    registry.get_adapter.side_effect = ValueError(
        "Unsupported ATS provider: workday"
    )

    service = IngestionService(registry)

    boards = [
        ATSBoard(
            provider="greenhouse",  # We'll override this below
            board_id="example",
            company_name="Example",
        )
    ]

    boards[0] = ATSBoard.model_construct(
        provider="workday",
        board_id="example",
        company_name="Example",
    )

    async with httpx.AsyncClient() as client:
        with pytest.raises(
            ValueError,
            match="Unsupported ATS provider: workday",
        ):
            await service.ingest(boards, client)

    registry.get_adapter.assert_called_once_with("workday")