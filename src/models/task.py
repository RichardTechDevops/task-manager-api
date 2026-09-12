"""Task data models. Designed so storage can later move from memory to a database."""

from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator


def utc_now() -> datetime:
    """Return a timezone-aware UTC timestamp without microseconds."""
    return datetime.now(timezone.utc).replace(microsecond=0)


class TaskStatus(str, Enum):
    """Allowed task lifecycle values."""

    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    """Payload for creating a task."""

    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: TaskStatus = TaskStatus.TODO

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        """Reject titles that only contain whitespace."""
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title cannot be empty")
        return cleaned


class TaskUpdate(BaseModel):
    """Payload for updating an existing task. Omitted fields stay unchanged."""

    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TaskStatus] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        """Reject blank titles when the field is provided."""
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title cannot be empty")
        return cleaned


class Task(BaseModel):
    """Persisted task representation returned by the API."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        """Serialize timestamps as ISO-8601 UTC strings with a Z suffix."""
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
