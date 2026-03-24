from datetime import datetime
from pydantic import BaseModel, Field


class EventCreate(BaseModel):
    title: str
    event_type: str | None = None
    location: str | None = None
    event_date: datetime | None = None
    notes: str | None = None
    keywords: str | None = None
    brand_voice: str | None = None
    cta: str | None = None


class PostCreate(BaseModel):
    event_id: int
    asset_id: int
    publish_at: datetime = Field(
            description="Local wall-clock time without timezone suffix , e.g., 2026-03-23-00:01:02"
        )
    publish_timezone: str = Field(
            default="UTC",
            description="IANA timezone name, e.g., America/Los_Angeles",
    )


class GenerateRequest(BaseModel):
    post_id: int


class ApproveRequest(BaseModel):
    caption_final: str
    hashtags_final: str
    accessibility_text: str | None = None

class TimeConvertRequest(BaseModel):
    local_datetime: datetime = Field(
            description="Local wall-clock time without timezone suffix, e.g., 2026-03-23T02:03:04"
    )
    timezone: str = Field(
            description="IANA timezone name, e.g., America/Los_Angeles"
    )

class TimeConvertResponse(BaseModel):
    local_datetime: str
    timezone: str
    utc_datetime: str
