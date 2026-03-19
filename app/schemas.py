from datetime import datetime
from pydantic import BaseModel


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
    publish_at: datetime


class GenerateRequest(BaseModel):
    post_id: int


class ApproveRequest(BaseModel):
    caption_final: str
    hashtags_final: str
    accessibility_text: str | None = None
