from datetime import date
from typing import Dict, List, Optional

from pydantic import BaseModel, Field

from .goal import GoalType


# External or personal constraints that influence planning.
class ConstraintInput(BaseModel):
    type: str
    description: str
    valid_until: Optional[date] = None
    priority: Optional[str] = None


# Optional goal context provided to the planner.
class PlanGoalInput(BaseModel):
    title: str
    type: GoalType
    deadline: date
    memory_id: Optional[str] = None
    budget: Optional[float] = None
    weekly_hours: Optional[int] = None
    preferences: Dict[str, object] = Field(default_factory=dict)


# Request payload for generating a plan or daily briefing.
class PlanRequest(BaseModel):
    user_context: str = "I am ready for the day."
    timezone: str = "UTC"
    goal: Optional[PlanGoalInput] = None
    constraints: List[ConstraintInput] = Field(default_factory=list)
    current_state: Dict[str, object] = Field(default_factory=dict)


# Milestone output from the planning engine.
class PlanMilestone(BaseModel):
    id: str
    title: str
    target_date: date
    definition_of_done: str
    order: int


# Task output from the planning engine.
class PlanTask(BaseModel):
    id: str
    title: str
    due_date: date
    milestone_id: str
    priority: str = "medium"
    estimated_time: Optional[float] = None
    depends_on: List[str] = Field(default_factory=list)


# Supporting artifacts (links, notes, docs) surfaced by planning.
class PlanArtifact(BaseModel):
    id: str
    title: str
    type: str
    content: str


# Structured plan response from the planning engine.
class PlanResponse(BaseModel):
    date: date
    focus: str
    milestones: List[PlanMilestone] = Field(default_factory=list)
    tasks: List[PlanTask] = Field(default_factory=list)
    artifacts: List[PlanArtifact] = Field(default_factory=list)
    message: str
    warnings: List[str] = Field(default_factory=list)
