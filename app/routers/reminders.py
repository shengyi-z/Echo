from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db.database import get_db
from app.db.models import Reminder
from app.db.schemas import ReminderCreate, ReminderOut
from app.services.scheduler import scheduler
from dateutil import parser as dtparser

router = APIRouter()

@router.post("/", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    try:
        trigger_time = dtparser.parse(payload.trigger_at)
    except ValueError:
        raise HTTPException(
            status_code=400, detail="Invalid trigger time format")

    reminder = Reminder(
        user_id=payload.user_id,
        task_id=payload.task_id,
        trigger_at=trigger_time,
        message=payload.message,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    scheduler.schedule_reminder(reminder.id, reminder.trigger_at)
    return reminder


@router.get("/", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db)):
    return db.query(Reminder).order_by(Reminder.created_at.desc()).all()
