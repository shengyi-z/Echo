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
    thread_id: str = Field(...,
                           description="Backboard thread ID for AI conversation context")
    memory_id: Optional[str] = Field(
        None, description="Optional memory ID for linking to external context")
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


# Insights with structured formatting
class PlanInsights(BaseModel):
    overview: Optional[str] = None
    key_points: List[str] = Field(default_factory=list)
    precautions: List[str] = Field(default_factory=list)
    progression_guidelines: Optional[str] = None
    scientific_basis: Optional[str] = None
    adjustments: Optional[str] = None
    raw_text: Optional[str] = None  # Fallback for unstructured insights


# Resource links and references
class PlanResource(BaseModel):
    title: Optional[str] = None
    url: str
    category: Optional[str] = None


# Structured plan response from the planning engine.
class PlanResponse(BaseModel):
    date: date
    focus: str
    milestones: List[PlanMilestone] = Field(default_factory=list)
    tasks: List[PlanTask] = Field(default_factory=list)
    artifacts: List[PlanArtifact] = Field(default_factory=list)
    insights: Optional[PlanInsights] = None
    resources: List[PlanResource] = Field(default_factory=list)
    message: str
    warnings: List[str] = Field(default_factory=list)
