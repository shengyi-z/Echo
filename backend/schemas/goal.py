1
from datetime import date
from enum import Enum
from typing import List, Optional
from uuid import UUID

from pydantic import BaseModel, Field

from .task import TaskCreateEmbedded, TaskOut

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


# Allowed goal lifecycle states.
class GoalStatus(str, Enum):
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


# Allowed milestone lifecycle states.
class MilestoneStatus(str, Enum):
    NOT_STARTED = "not-started"
    IN_PROGRESS = "in-progress"
    COMPLETED = "completed"
    PAUSED = "paused"
    CANCELLED = "cancelled"


# Supported goal categories.
class GoalType(str, Enum):
    VISA = "visa"
    LANGUAGE = "language"
    FITNESS = "fitness"
    STUDY = "study"
    CAREER = "career"
    FINANCE = "finance"
    HEALTH = "health"
    TRAVEL = "travel"
    OTHER = "other"


# Shared milestone fields for create/update/output payloads.
class MilestoneBase(SchemaBase):
    title: str
    target_date: date
    definition_of_done: str
    order: Optional[int] = None
    status: MilestoneStatus = MilestoneStatus.NOT_STARTED


# Required fields when creating a milestone (with optional tasks).
class MilestoneCreate(MilestoneBase):
    tasks: List[TaskCreateEmbedded] = Field(default_factory=list)


# Optional fields for partial milestone updates.
class MilestoneUpdate(SchemaBase):
    title: Optional[str] = None
    target_date: Optional[date] = None
    definition_of_done: Optional[str] = None
    order: Optional[int] = None
    status: Optional[MilestoneStatus] = None


# Response shape for milestone reads.
class MilestoneOut(MilestoneBase):
    id: UUID
    goal_id: UUID
    tasks: List[TaskOut] = Field(default_factory=list)


# Shared goal fields for create/update/output payloads.
class GoalBase(SchemaBase):
    memory_id: str
    title: str
    type: GoalType
    deadline: date
    budget: Optional[float] = None
    weekly_hours: Optional[int] = None
    status: GoalStatus = GoalStatus.NOT_STARTED


# Required fields when creating a goal (with optional milestones).
class GoalCreate(GoalBase):
    milestones: List[MilestoneCreate] = Field(default_factory=list)


# Optional fields for partial goal updates.
class GoalUpdate(SchemaBase):
    memory_id: Optional[str] = None
    title: Optional[str] = None
    type: Optional[GoalType] = None
    deadline: Optional[date] = None
    budget: Optional[float] = None
    weekly_hours: Optional[int] = None
    status: Optional[GoalStatus] = None


# Response shape for goal reads.
class GoalOut(GoalBase):
    id: UUID
    milestones: List[MilestoneOut] = Field(default_factory=list)
    tasks: List[TaskOut] = Field(default_factory=list)
