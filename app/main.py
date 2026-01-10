import logging
from fastapi import FastAPI, Depends
from fastapi import HTTPException
from sqlalchemy.orm import Session
from app.database import Base, engine, get_db
from app.models import Task, Reminder, BackboardThread
from app.schemas import TaskCreate, TaskOut, ReminderCreate, ReminderOut, ChatRequest, ChatResponse
from app.scheduler import scheduler
from app.backboard_client import backboard
from app.llm_client import llm
from dateutil import parser as dtparser

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Echo Assistant API")


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    # Daily digest at 8am UTC by default
    scheduler.schedule_daily_digest()


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

@app.post("/chat", response_model=ChatResponse)
def chat(req: ChatRequest, db: Session = Depends(get_db)):
    if not req.message:
        raise HTTPException(status_code=400, detail="message required")

    thread_id = None
    if req.user_id:
        bt = db.query(BackboardThread).filter(BackboardThread.user_id == req.user_id).first()
        if bt:
            thread_id = bt.thread_id
        else:
            tid = backboard.get_or_create_thread(req.user_id)
            if tid:
                bt = BackboardThread(user_id=req.user_id, thread_id=tid)
                db.add(bt)
                db.commit()
                db.refresh(bt)
                thread_id = tid

    memory = backboard.retrieve_memory(thread_id, req.message) if thread_id else ""
    out_text = llm.generate(req.message, memory)
    action, when = llm.parse_action(out_text)

    if action == "remind" and when:
        try:
            due_at = dtparser.parse(when)
        except Exception:
            raise HTTPException(status_code=400, detail="invalid time format in action")
        # Create a generic task if none exists
        task = Task(user_id=req.user_id, title=req.message, description=None)
        db.add(task)
        db.commit()
        db.refresh(task)
        reminder = Reminder(task_id=task.id, due_at=due_at, timezone="UTC")
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        job_id = scheduler.schedule_reminder(reminder.id, reminder.due_at)
        reminder.scheduled_job_id = job_id
        db.add(reminder)
        db.commit()
        db.refresh(reminder)
        return ChatResponse(action="remind", time=when)

    return ChatResponse(text=out_text)
