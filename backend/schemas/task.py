1
from datetime import date
from enum import Enum
from typing import Optional
from uuid import UUID

from pydantic import BaseModel

try:
    from pydantic import ConfigDict
except ImportError:  # pragma: no cover - pydantic v1 fallback
    ConfigDict = None


# Base schema with ORM compatibility for pydantic v1/v2.
class SchemaBase(BaseModel):
    if ConfigDict:
        model_config = ConfigDict(from_attributes=True)
    else:
        class Config:
            orm_mode = True


# Allowed task lifecycle states.
class TaskStatus(str, Enum):
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


# Allowed task priority levels.
class TaskPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


# Shared task fields for create/update/output payloads.
class TaskBase(SchemaBase):
    title: str
    due_date: date
    priority: TaskPriority = TaskPriority.MEDIUM
    status: TaskStatus = TaskStatus.NOT_STARTED
    estimated_time: Optional[float] = None


# Required fields when creating a task.
class TaskCreate(TaskBase):
    goal_id: UUID
    milestone_id: UUID


# Embedded task shape used inside milestone creation.
class TaskCreateEmbedded(TaskBase):
    pass


# Optional fields for partial task updates.
class TaskUpdate(SchemaBase):
    title: Optional[str] = None
    due_date: Optional[date] = None
    priority: Optional[TaskPriority] = None
    status: Optional[TaskStatus] = None
    estimated_time: Optional[float] = None
    milestone_id: Optional[UUID] = None


# Response shape for task reads.
class TaskOut(TaskBase):
    id: UUID
    goal_id: UUID
    milestone_id: UUID
