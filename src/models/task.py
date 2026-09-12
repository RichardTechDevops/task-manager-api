# 任务数据模型。
# 用 Pydantic 做入参校验和 JSON 序列化；status 用枚举限制取值。
from datetime import datetime, timezone
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field, field_serializer, field_validator


def utc_now() -> datetime:
    # 统一用 UTC，去掉微秒，输出形如 2026-01-01T00:00:00Z。
    return datetime.now(timezone.utc).replace(microsecond=0)


class TaskStatus(str, Enum):
    # 作业规定只允许这三个状态。
    TODO = "todo"
    IN_PROGRESS = "in_progress"
    DONE = "done"


class TaskCreate(BaseModel):
    # POST /tasks 请求体。title 必填，description 和 status 有默认值。
    title: str = Field(..., min_length=1, max_length=200)
    description: str = Field(default="", max_length=2000)
    status: TaskStatus = TaskStatus.TODO

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: str) -> str:
        # 只含空格的标题也视为非法，配合全局异常处理返回 400。
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title cannot be empty")
        return cleaned


class TaskUpdate(BaseModel):
    # PUT /tasks/{id} 请求体。字段都可选，没传的字段保持原值。
    title: Optional[str] = Field(default=None, min_length=1, max_length=200)
    description: Optional[str] = Field(default=None, max_length=2000)
    status: Optional[TaskStatus] = None

    @field_validator("title")
    @classmethod
    def title_must_not_be_blank(cls, value: Optional[str]) -> Optional[str]:
        # None 表示调用方没改 title；空字符串或空白则拒绝。
        if value is None:
            return value
        cleaned = value.strip()
        if not cleaned:
            raise ValueError("title cannot be empty")
        return cleaned


class Task(BaseModel):
    # 接口返回的完整任务对象，对应作业数据模型。
    id: str = Field(default_factory=lambda: str(uuid4()))
    title: str
    description: str
    status: TaskStatus
    created_at: datetime
    updated_at: datetime

    @field_serializer("created_at", "updated_at")
    def serialize_datetime(self, value: datetime) -> str:
        # 序列化成作业要求的 ISO8601 UTC 字符串。
        return value.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
