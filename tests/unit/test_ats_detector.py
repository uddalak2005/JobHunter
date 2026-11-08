import pytest

from ingest.discovery.ats_detector import detect_ats_board


@pytest.mark.parametrize(
    ("url", "provider", "board_id"),
    [
        (
            "https://boards.greenhouse.io/stripe/jobs/123",
            "greenhouse",
            "stripe",
        ),
        (
            "https://jobs.lever.co/linear/abc123",
            "lever",
            "linear",
        ),
        (
            "https://jobs.ashbyhq.com/Linear/abc123",
            "ashby",
            "Linear",
        ),
    ],
)
def test_detects_board_from_board_or_job_url(url, provider, board_id):
    board = detect_ats_board(url, "Example Company")

    assert board is not None
    assert board.provider == provider
    assert board.board_id == board_id
    assert board.company_name == "Example Company"


@pytest.mark.parametrize(
    "url",
    [
        "https://careers.example.com/jobs",
        "https://jobs.ashbyhq.com.evil.example/linear",
        "https://jobs.lever.co/",
        "javascript:alert(1)",
        "not a URL",
    ],
)
def test_unsupported_or_malformed_urls_return_none(url):
    assert detect_ats_board(url, "Example Company") is None


def test_blank_company_name_returns_none():
    assert detect_ats_board("https://jobs.lever.co/linear", " ") is None