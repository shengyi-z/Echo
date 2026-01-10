import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from apscheduler.triggers.date import DateTrigger
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy.orm import Session
from app.db.database import engine, SessionLocal
from app.db.models import Reminder, ReminderStatus, Task, Channel
from app.services.notifications import send_notification

log = logging.getLogger(__name__)


class Scheduler:
    def __init__(self):
        self.jobstores = {
            'default': SQLAlchemyJobStore(engine=engine)
        }
        self.scheduler = BackgroundScheduler(jobstores=self.jobstores)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            log.info("Scheduler started")

    def shutdown(self):
        if self.scheduler.running:
            self.scheduler.shutdown(wait=False)
            log.info("Scheduler stopped")

    def schedule_reminder(self, reminder_id: str, run_at: datetime):
        trigger = DateTrigger(run_date=run_at)
        job = self.scheduler.add_job(
            self._run_reminder, trigger=trigger, args=[reminder_id])
        return job.id

    def schedule_daily_digest(self, hour: int = 8, timezone: str = "UTC"):
        """Schedule a daily digest at the specified hour."""
        trigger = CronTrigger(hour=hour, minute=0, timezone=timezone)
        self.scheduler.add_job(self._run_daily_digest, trigger=trigger)
        log.info(f"Daily digest scheduled at {hour:02d}:00 {timezone}")

    @staticmethod
    def _run_reminder(reminder_id: str):
        db: Session = SessionLocal()
        try:
            reminder = db.query(Reminder).filter(
                Reminder.id == reminder_id).first()
            if not reminder:
                log.warning(f"Reminder {reminder_id} missing")
                return
            if reminder.status != ReminderStatus.scheduled:
                log.info(
                    f"Reminder {reminder_id} status {reminder.status}, skipping")
                return
            msg = f"Reminder for task {reminder.task_id} due at {reminder.due_at}"
            send_notification(db, reminder.channel, msg, reminder.id)
            reminder.status = ReminderStatus.sent
            reminder.last_attempt_at = datetime.utcnow()
            db.add(reminder)
            db.commit()
        except Exception as e:
            log.exception(f"Reminder {reminder_id} failed: {e}")
        finally:
            db.close()

    @staticmethod
    def _run_daily_digest():
        """Generate and send daily digest of pending tasks."""
        db: Session = SessionLocal()
        try:
            tasks = db.query(Task).filter(Task.status != 'done').order_by(Task.created_at.asc()).limit(20).all()
            if not tasks:
                log.info("No pending tasks for daily digest")
                return
            
            summary = "\n".join([f"- {t.title}: {t.description or ''}" for t in tasks])
            message = f"Daily Digest\n\nPending tasks:\n{summary}"
            send_notification(db, Channel.email, message, reminder_id="digest")
            log.info("Daily digest sent successfully")
        except Exception as e:
            log.exception(f"Daily digest failed: {e}")
        finally:
            db.close()


scheduler = Scheduler()
