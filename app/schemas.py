from datetime import datetime

from pydantic import BaseModel, Field


# =========================
# EVENT
# =========================

class EventCreate(BaseModel):
    title: str
    event_type: str | None = None
    location: str | None = None
    event_date: datetime | None = None
    event_timezone: str | None = None
    recap: str | None = None
    keywords: str | None = None
    vendors: str | None = None
    event_guidance: str | None = None


class EventResponse(BaseModel):
    id: int
    title: str
    event_type: str | None = None
    location: str | None = None
    event_date: datetime | None = None
    event_timezone: str | None = None
    recap: str | None = None
    keywords: str | None = None
    vendors: str | None = None
    event_guidance: str | None = None


# =========================
# ASSETS
# =========================

class AssetResponse(BaseModel):
    id: int
    event_id: int | None
    file_path: str
    media_type: str
    analysis_status: str
    vision_summary_generated: str | None = None
    accessibility_text_generated: str | None = None
    accessibility_text_final: str | None = None
    analysis_error_message: str | None = None
    analysis_user_correction: str | None = None

class AssetAnalyzeRequest(BaseModel):
    user_correction: str | None = None

class AssetAnalyzeResponse(BaseModel):
    asset_id: int
    analysis_status: str
    vision_summary_generated: str | None = None
    accessibility_text_generated: str | None = None
    analysis_error_message: str | None = None


class AssetApproveRequest(BaseModel):
    accessibility_text_final: str


class AssetApproveResponse(BaseModel):
    asset_id: int
    analysis_status: str
    accessibility_text_final: str


# =========================
# POST DRAFT GENERATION
# =========================

class PostDraftCreate(BaseModel):
    event_id: int | None = None
    asset_id: int
    brand_voice: str | None = None
    cta_goal: str | None = Field(
        default=None,
        description="High-level CTA intent, e.g. encourage follows, inquiries, bookings, or clicks.",
    )
    generation_notes: str | None = None


class PostDraftCreateResponse(BaseModel):
    post_id: int
    status: str

class PostGenerateRequest(BaseModel):
    seed_caption: str | None = None

class PostDraftContentUpdate(BaseModel):
    draft_caption_current: str | None = None
    draft_hashtags_current: str | None = None
    draft_accessibility_current: str | None = None

class PostGenerationResponse(BaseModel):
    post_id: int
    status: str
    caption_option_1: str | None = None
    caption_option_2: str | None = None
    caption_option_3: str | None = None
    hashtags: list[str] = Field(default_factory=list)
    accessibility_text: str | None = None
    seo_keywords: list[str] = Field(default_factory=list)
    visual_summary: str | None = None

class PostDraftUpdate(BaseModel):
    brand_voice: str | None = None
    cta_goal: str | None = None
    generation_notes: str | None = None


# =========================
# POST APPROVAL
# =========================

class ApprovePostRequest(BaseModel):
    caption_final: str
    hashtags_final: list[str]
    accessibility_text: str | None = None


class ApprovedPostResponse(BaseModel):
    approved_post_id: int
    status: str


# =========================
# SCHEDULING
# =========================

class ScheduleCreate(BaseModel):
    publish_at: datetime = Field(
        description="Local wall-clock time WITHOUT timezone suffix, e.g. 2026-03-23T03:04:05"
    )
    publish_timezone: str = Field(
        default="UTC",
        description="IANA timezone name, e.g. America/Los_Angeles",
    )


class ScheduleResponse(BaseModel):
    schedule_id: int
    status: str


# =========================
# TIME UTILITIES
# =========================

class TimeConvertRequest(BaseModel):
    local_datetime: datetime = Field(
        description="Local wall-clock time WITHOUT timezone suffix"
    )
    timezone: str = Field(
        description="IANA timezone name"
    )


class TimeConvertResponse(BaseModel):
    local_datetime: str
    timezone: str
    utc_datetime: str
