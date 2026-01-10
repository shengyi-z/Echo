import logging
from fastapi import FastAPI
from app.db.database import Base, engine
from app.services.scheduler import scheduler
from app.routers import tasks, reminders, chat

logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Echo Assistant API")

app.include_router(tasks.router, prefix="/tasks", tags=["tasks"])
app.include_router(reminders.router, prefix="/reminders", tags=["reminders"])
app.include_router(chat.router, prefix="/chat", tags=["chat"])


@app.on_event("startup")
def on_startup():
    Base.metadata.create_all(bind=engine)
    scheduler.start()
    # Daily digest at 8am UTC by default
    scheduler.schedule_daily_digest()


@app.on_event("shutdown")
def on_shutdown():
    scheduler.shutdown()
