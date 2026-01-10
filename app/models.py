import uuid
from datetime import datetime
from sqlalchemy import Column, String, DateTime, Enum, ForeignKey
from sqlalchemy.orm import relationship
from app.database import Base
import enum


class TaskStatus(str, enum.Enum):
    todo = "todo"
    doing = "doing"
    done = "done"


class Channel(str, enum.Enum):
    email = "email"
    sms = "sms"
    push = "push"


class Task(Base):
    __tablename__ = "tasks"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, nullable=True)
    title = Column(String, nullable=False)
    description = Column(String, nullable=True)
    status = Column(Enum(TaskStatus), default=TaskStatus.todo, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow,
                        onupdate=datetime.utcnow)

    reminders = relationship("Reminder", back_populates="task")


class ReminderStatus(str, enum.Enum):
    scheduled = "scheduled"
    sent = "sent"
    canceled = "canceled"


class Reminder(Base):
    __tablename__ = "reminders"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    task_id = Column(String, ForeignKey("tasks.id"), nullable=False)
    due_at = Column(DateTime, nullable=False)
    timezone = Column(String, nullable=False, default="UTC")
    channel = Column(Enum(Channel), nullable=False, default=Channel.email)
    status = Column(Enum(ReminderStatus), nullable=False,
                    default=ReminderStatus.scheduled)
    last_attempt_at = Column(DateTime, nullable=True)
    scheduled_job_id = Column(String, nullable=True)

    task = relationship("Task", back_populates="reminders")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    reminder_id = Column(String, ForeignKey("reminders.id"), nullable=False)
    channel = Column(Enum(Channel), nullable=False)
    sent_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    result = Column(String, nullable=False, default="success")
    provider_id = Column(String, nullable=True)


class UserPreference(Base):
    __tablename__ = "user_preferences"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False)
    default_channel = Column(
        Enum(Channel), nullable=False, default=Channel.email)
    timezone = Column(String, nullable=False, default="UTC")

class BackboardThread(Base):
    __tablename__ = "backboard_threads"

    id = Column(String, primary_key=True, default=lambda: str(uuid.uuid4()))
    user_id = Column(String, unique=True, nullable=False)
    thread_id = Column(String, nullable=False)
