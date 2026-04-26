from datetime import UTC, datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base
from app.domain.statuses import AssetStatus, PostStatus, ScheduleStatus

"""
Core database models for Lorewell.

Lorewell is structured around transforming real-world events into publishable content:

Event → Asset → Post → ApprovedPost → Schedule

Each layer adds structure and intent:
- Events provide context
- Assets provide visual input
- Posts generate content
- ApprovedPosts finalize content
- Schedules execute publishing

This separation keeps content modular, reusable, and composable.
"""

class Event(Base):
    """
    Represents a real-world occurrence or project that generated media.

    An Event acts as a shared context container for multiple Assets.
    It stores both factual information (what happened) and editorial guidance
    (how the system should interpret and present the event).

    Events are not posts — they are source material from which posts are created.

    title: str
    # Human-readable name of the event (e.g., "Smith Wedding Reception")

    event_type: str | None
    # Category of event (e.g., wedding, club set, corporate)

    location: str | None
    # Where the event took place

    event_date: datetime | None
    # Primary timestamp anchor for the event (not necessarily full duration)

    event_timezone: str | None
    # What timezone did this happen at

    recap: str | None
    # Factual summary of what happened at the event (memory + context)

    keywords: str | None
    # Optional searchable or thematic keywords (SEO + tagging support)

    vendors: str | None
    # Other collaborators or vendors involved in the event

    event_guidance: str | None
    # Editorial instruction for how content from this event should be framed

    created_at: datetime
    # When this event record was created
    """

    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    event_timezone: Mapped[String | None] = mapped_column(String, nullable=True)
    recap: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendors: Mapped[str | None] = mapped_column(Text, nullable=True)
    event_guidance: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    assets = relationship("Asset", back_populates="event", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="event", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)

    file_path: Mapped[str] = mapped_column(Text)
    display_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    media_type: Mapped[str] = mapped_column(String(20))

    captured_at_guess: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    captured_at_guess_source: Mapped[str | None] = mapped_column(String(30), nullable=True)
    captured_at_guess_confidence: Mapped[str | None] = mapped_column(String(30), nullable=True)
    captured_at_guess_matched_text: Mapped[str | None] = mapped_column(String(64), nullable=True)



    vision_summary_generated: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_text_generated: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_text_final: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis_status: Mapped[str] = mapped_column(String(30), default=AssetStatus.PENDING)
    analysis_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_user_correction: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    event = relationship("Event", back_populates="assets")

class Post(Base):
    """
    Represents a draft or generated piece of social media content.

    A Post is created by selecting an Asset (and optionally its Event),
    and applying generation parameters such as brand voice and CTA goals.

    Posts go through stages: draft → generated → approved.
    They do not directly publish; ApprovedPosts handle final output.

    primary_asset_id: int
    # The main asset used to generate this post

    event_id: int | None
    # Optional event context associated with this post

    brand_voice: str | None
    # Tone/style for generation (e.g., energetic, elegant)

    cta_goal: str | None
    # High-level call-to-action intention (not literal phrasing)

    generation_notes: str | None
    # Additional user instructions for generation

    generated_caption_options: str | None
    # AI-generated caption suggestion (current primary)

    generated_hashtag_options: str | None
    # AI-generated hashtags

    generated_accessibility_options: str | None
    # AI-generated accessibility text suggestion

    status: str
    # draft → generated → approved

    error_message: str | None
    # Error message if generation fails
    """
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    primary_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))

    brand_voice: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    working_title: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_caption_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_hashtag_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_accessibility_options: Mapped[str | None] = mapped_column(Text, nullable=True)

    draft_caption_current: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_hashtags_current: Mapped[str | None] = mapped_column(Text, nullable=True)
    draft_accessibility_current: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default=PostStatus.DRAFT)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    event = relationship("Event", back_populates="posts")
    primary_asset = relationship("Asset", foreign_keys=[primary_asset_id])
    approved_posts = relationship("ApprovedPost", back_populates="post", cascade="all, delete-orphan")


class ApprovedPost(Base):
    """
    Represents a finalized, user-approved version of a Post ready for scheduling.

    This separates editable/generated content from locked-in content
    that will be published.

    ApprovedPosts are immutable records of publishing intent.

    post_id: int
    # Source Post this approval is based on

    selected_asset_id: int
    # Asset chosen for publishing (currently single, future multi-asset)

    caption_final: str
    # Final caption text

    hashtags_final: str
    # Final hashtags string

    accessibility_text: str
    # Final accessibility text used for publishing
    """
    __tablename__ = "approved_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    selected_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))

    caption_final: Mapped[str] = mapped_column(Text)
    hashtags_final: Mapped[str] = mapped_column(Text)
    accessibility_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    approved_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    post = relationship("Post", back_populates="approved_posts")
    selected_asset = relationship("Asset", foreign_keys=[selected_asset_id])
    schedules = relationship("Schedule", back_populates="approved_post", cascade="all, delete-orphan")


class Schedule(Base):
    """
    Represents a scheduled publishing job for an ApprovedPost.

    Schedules manage when and how posts are published, including
    tracking execution state, failures, and retries.

    This is the system's bridge between content and actual posting.

    approved_post_id: int
    # The approved post to publish

    publish_at: datetime
    # UTC timestamp when publishing should occur

    publish_timezone: str
    # Original timezone used for scheduling (for UI reference)

    status: str
    # scheduled → publishing → published / failed

    published_instagram_id: str | None
    # ID returned by Instagram after publishing

    error_message: str | None
    # Final error if publishing fails

    last_attempt_error: str | None
    # Most recent error during publishing attempts

    publish_attempts: int
    # Number of times publishing has been attempted

    publishing_started_at: datetime | None
    # When the current publish attempt began (for stale detection)

    failure_acknowledged: Bool
    # If the schedule fails, whether or not User has acknowledged the failed schedule. It's an Inbox system
    """
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approved_post_id: Mapped[int] = mapped_column(ForeignKey("approved_posts.id"))

    publish_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    publish_timezone: Mapped[str] = mapped_column(String(100), default="UTC")

    status: Mapped[str] = mapped_column(String(30), default=ScheduleStatus.SCHEDULED)
    published_instagram_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    failure_acknowledged: Mapped[bool] = mapped_column(Boolean, default=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    publishing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    publish_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_error: Mapped[str| None] = mapped_column(Text, nullable=True)

    approved_post = relationship("ApprovedPost", back_populates="schedules")

