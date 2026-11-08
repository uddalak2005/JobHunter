import re
from urllib.parse import unquote, urlsplit

from typing import Literal

from ingest.schemas import ATSBoard

ATSProvider = Literal["greenhouse", "lever", "ashby"]

_SLUG_RE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")

_PROVIDER_HOSTS : dict[str, ATSProvider]= {
    "boards.greenhouse.io": "greenhouse",
    "job-boards.greenhouse.io": "greenhouse",
    "jobs.lever.co": "lever",
    "jobs.ashbyhq.com": "ashby",
}

def detect_ats_board(career_url: str, company_name: str) -> ATSBoard | None:
    """
    Detects the ATS board from a given career URL and company name.

    Args:
        career_url (str): The career URL to analyze.
        company_name (str): The name of the company.

    Returns:
        ATSBoard | None: An ATSBoard object if detected, otherwise None.
    """
    url = career_url.strip()
    company = company_name.strip()
    
    if not url or not company:
        return None
    
    try:
        parsed = urlsplit(url)
        host = (parsed.hostname or "").lower()
    except ValueError:
        return None
    
    if parsed.scheme not in ("http", "https"):
        return None
    
    provider = _PROVIDER_HOSTS.get(host)
    if not provider:
        return None
    
    path_parts = [
        unquote(part) for part in parsed.path.strip("/").split("/") if part
    ]
    
    if not path_parts:
        return None
    
    board_id = path_parts[0]
    
    if not _SLUG_RE.fullmatch(board_id):
        return None
    
    return ATSBoard(provider=provider, board_id=board_id, company_name=company)