from sqlalchemy import Column, String, Date, Float, Integer
from sqlalchemy.orm import relationship
from sqlalchemy.dialects.postgresql import UUID
import uuid

from ..core.db import Base


class Goal(Base):
    """
    Represents a high-level goal in the database.
    """
    __tablename__ = "goals"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    memory_id = Column(String, nullable=False, unique=True, index=True)
    title = Column(String, nullable=False, index=True)
    type = Column(String, nullable=False)
    deadline = Column(Date, nullable=False)
    budget = Column(Float, nullable=True)
    weekly_hours = Column(Integer, nullable=True)
    status = Column(String, nullable=False, default="not-started")

    # Relationships
    milestones = relationship("Milestone", back_populates="goal", cascade="all, delete-orphan")
    tasks = relationship("Task", back_populates="goal", cascade="all, delete-orphan")
