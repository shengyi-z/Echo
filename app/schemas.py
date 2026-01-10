from datetime import datetime
from pydantic import BaseModel, Field
from typing import Optional
from app.models import TaskStatus, Channel, ReminderStatus


class TaskCreate(BaseModel):
    user_id: Optional[str] = None
    title: str
    description: Optional[str] = None


class TaskOut(BaseModel):
    id: str
    user_id: Optional[str] = None
    title: str
    description: Optional[str] = None
    status: TaskStatus
    created_at: datetime
    updated_at: Optional[datetime] = None

    class Config:
        from_attributes = True


class ReminderCreate(BaseModel):
    task_id: str
    due_at: datetime
    timezone: Optional[str] = None
    channel: Optional[Channel] = Channel.email


class ReminderOut(BaseModel):
    id: str
    task_id: str
    due_at: datetime
    timezone: str
    channel: Channel
    status: ReminderStatus
    last_attempt_at: Optional[datetime] = None
    scheduled_job_id: Optional[str] = None

    class Config:
        from_attributes = True
