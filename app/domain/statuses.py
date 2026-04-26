from enum import StrEnum


class AssetStatus(StrEnum):
    PENDING = "pending"
    ANALYZED = "analyzed"
    APPROVED = "approved"
    FAILED = "failed"


class PostStatus(StrEnum):
    DRAFT = "draft"
    GENERATED = "generated"
    APPROVED = "approved"


class ScheduleStatus(StrEnum):
    SCHEDULED = "scheduled"
    PUBLISHING = "publishing"
    PUBLISHED = "published"
    FAILED = "failed"
