from sqlalchemy import Column, String, Date, Integer, ForeignKey
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.db import Base


class Milestone(Base):
    """
    Represents a significant milestone within a larger goal.
    """
    __tablename__ = "milestones"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    goal_id = Column(UUID(as_uuid=True), ForeignKey("goals.id"), nullable=False)
    title = Column(String, nullable=False)
    target_date = Column(Date, nullable=False)
    definition_of_done = Column(String, nullable=False)
    order = Column(Integer, nullable=False)
    status = Column(String, nullable=False, default="not-started")

    # Relationships
    goal = relationship("Goal", back_populates="milestones")
    tasks = relationship("Task", back_populates="milestone", cascade="all, delete-orphan")
