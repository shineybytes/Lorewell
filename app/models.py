from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db import Base


class Event(Base):
    __tablename__ = "events"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255))
    event_type: Mapped[str | None] = mapped_column(String(100), nullable=True)
    location: Mapped[str | None] = mapped_column(String(255), nullable=True)
    event_date: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    keywords: Mapped[str | None] = mapped_column(Text, nullable=True)
    vendors: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    assets = relationship("Asset", back_populates="event", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="event", cascade="all, delete-orphan")


class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)

    file_path: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(String(20))

    vision_summary_generated: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_text_generated: Mapped[str | None] = mapped_column(Text, nullable=True)
    accessibility_text_final: Mapped[str | None] = mapped_column(Text, nullable=True)

    analysis_status: Mapped[str] = mapped_column(String(30), default="pending")
    analysis_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    analysis_user_correction: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    event = relationship("Event", back_populates="assets")


class Post(Base):
    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int | None] = mapped_column(ForeignKey("events.id"), nullable=True)
    primary_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))

    brand_voice: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_goal: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_caption_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_hashtag_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_accessibility_options: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="draft")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    event = relationship("Event", back_populates="posts")
    primary_asset = relationship("Asset", foreign_keys=[primary_asset_id])
    approved_posts = relationship("ApprovedPost", back_populates="post", cascade="all, delete-orphan")


class ApprovedPost(Base):
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
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approved_post_id: Mapped[int] = mapped_column(ForeignKey("approved_posts.id"))

    publish_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    publish_timezone: Mapped[str] = mapped_column(String(100), default="UTC")

    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    published_instagram_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=lambda: datetime.now(UTC))

    publishing_started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    publish_attempts: Mapped[int] = mapped_column(Integer, default=0)
    last_attempt_error: Mapped[str| None] = mapped_column(Text, nullable=True)

    approved_post = relationship("ApprovedPost", back_populates="schedules")
