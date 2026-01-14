from sqlalchemy import Column, String, Date, Float, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.db import Base


class Task(Base):
    """
    Represents a concrete, actionable task within a milestone.
    """
    __tablename__ = "tasks"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey(
        "goals.id"), nullable=False)
    milestone_id = Column(UUID(as_uuid=True), ForeignKey(
        "milestones.id"), nullable=False)
    title = Column(String, nullable=False)
    due_date = Column(Date, nullable=False)
    priority = Column(String, nullable=False, default="medium")
    status = Column(String, nullable=False, default="not-started")
    estimated_time = Column(Float, nullable=True)

    # Relationships
    goal = relationship("Goal", back_populates="tasks")
    milestone = relationship("Milestone", back_populates="tasks")
    reminders = relationship(
        "Reminder", back_populates="task", cascade="all, delete-orphan")
    outgoing_dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.from_task_id",
        cascade="all, delete-orphan",
    )
    incoming_dependencies = relationship(
        "Dependency",
        foreign_keys="Dependency.to_task_id",
        cascade="all, delete-orphan",
    )
