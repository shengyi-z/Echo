import logging
from fastapi import FastAPI, Depends
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import Task, Reminder
from app.schemas import TaskCreate, TaskOut, ReminderCreate, ReminderOut
from app.scheduler import scheduler
from app.backboard_client import backboard

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Echo Assistant API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    scheduler.start()


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()


@app.post("/tasks", response_model=TaskOut)
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(
        user_id=payload.user_id,
        title=payload.title,
        description=payload.description,
    )
    db.add(task)
    db.commit()
    db.refresh(task)

    backboard.record_task_memory(
        task.user_id, task.id, task.title, task.description)
    return task


@app.get("/tasks", response_model=list[TaskOut])
def list_tasks(db: Session = Depends(get_db)):
    return db.query(Task).order_by(Task.created_at.desc()).all()


@app.post("/reminders", response_model=ReminderOut)
def create_reminder(payload: ReminderCreate, db: Session = Depends(get_db)):
    task = db.query(Task).filter(Task.id == payload.task_id).first()
    if not task:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Task not found")

    tz = payload.timezone or task and task.user_id and "UTC" or "UTC"
    reminder = Reminder(
        task_id=task.id,
        due_at=payload.due_at,
        timezone=tz,
        channel=payload.channel,
    )
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    job_id = scheduler.schedule_reminder(reminder.id, reminder.due_at)
    reminder.scheduled_job_id = job_id
    db.add(reminder)
    db.commit()
    db.refresh(reminder)

    return reminder


@app.get("/reminders", response_model=list[ReminderOut])
def list_reminders(db: Session = Depends(get_db)):
    return db.query(Reminder).order_by(Reminder.due_at.desc()).all()
