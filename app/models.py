from datetime import datetime
from sqlalchemy import String, Text, DateTime, ForeignKey, Integer
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
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    vendors: Mapped[str | None] = mapped_column(Text, nullable=True)

    assets = relationship("Asset", back_populates="event", cascade="all, delete-orphan")
    posts = relationship("Post", back_populates="event", cascade="all, delete-orphan")

class Asset(Base):
    __tablename__ = "assets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"), nullable=True)
    file_path: Mapped[str] = mapped_column(Text)
    media_type: Mapped[str] = mapped_column(String(20))  # image or video
    vision_summary: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="assets")

class Post(Base):
    __tablename__ = "posts"
    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id"))
    primary_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))

    brand_voice: Mapped[str | None] = mapped_column(Text, nullable=True)
    cta_instruction: Mapped[str | None] = mapped_column(Text, nullable=True)
    generation_notes: Mapped[str | None] = mapped_column(Text, nullable=True)

    generated_caption_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_hashtag_options: Mapped[str | None] = mapped_column(Text, nullable=True)
    generated_accessibility_options: Mapped[str | None] = mapped_column(Text, nullable=True)

    status: Mapped[str] = mapped_column(String(30), default="draft")
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    event = relationship("Event", back_populates="posts")
    approved_posts = relationship("ApprovedPost", back_populates="post", cascade="all, delete-orphan")

class ApprovedPost(Base):
    __tablename__ = "approved_posts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    post_id: Mapped[int] = mapped_column(ForeignKey("posts.id"))
    selected_asset_id: Mapped[int] = mapped_column(ForeignKey("assets.id"))

    caption_final: Mapped[str] = mapped_column(Text)
    hashtags_final: Mapped[str] = mapped_column(Text)
    accessibility_text: Mapped[str | None] = mapped_column(Text, nullable=True)

    approved_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    post = relationship("Post", back_populates="approved_posts")
    schedules = relationship("Schedule", back_populates="approved_post", cascade="all, delete-orphan")

class Schedule(Base):
    __tablename__ = "schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, index=True)
    approved_post_id: Mapped[int] = mapped_column(ForeignKey("approved_posts.id"))

    publish_at: Mapped[datetime] = mapped_column(DateTime, index=True) # UTC
    publish_timezone: Mapped[str] = mapped_column(String(100), default="UTC")

    status: Mapped[str] = mapped_column(String(30), default="scheduled")
    published_instagram_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    approved_post = relationship("ApprovedPost", back_populates="schedules")
