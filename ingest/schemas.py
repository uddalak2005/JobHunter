from datetime import datetime, timezone
from pydantic import BaseModel, Field, HttpUrl
from typing import Literal


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


class NormalizedJob(BaseModel):
    external_id: str
    title: str
    company: str

    location: str | None = None
    description: str | None = None
    apply_url: str | None = None
    source: str

    posted_at: datetime | None = None
    discovered_at: datetime = Field(default_factory=utcnow)


class ATSBoard(BaseModel):
    provider: Literal["greenhouse", "lever", "ashby"]
    board_id: str
    company_name: str
    career_url: HttpUrl | None = None
