from sqlalchemy import Column, ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
import uuid

from core.db import Base


class Dependency(Base):
    """
    Represents a dependency between two tasks.
    """
    __tablename__ = "dependencies"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    from_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)
    to_task_id = Column(UUID(as_uuid=True), ForeignKey("tasks.id"), nullable=False)

    __table_args__ = (
        UniqueConstraint("from_task_id", "to_task_id", name="uq_dependency_pair"),
    )

    # Relationships
    from_task = relationship("Task", foreign_keys=[from_task_id])
    to_task = relationship("Task", foreign_keys=[to_task_id])
