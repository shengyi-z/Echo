import logging
from app.models import Channel, Notification
from sqlalchemy.orm import Session

log = logging.getLogger(__name__)


def send_notification(db: Session, channel: Channel, message: str, reminder_id: str) -> Notification:
    # Placeholder: integrate Resend/Twilio/APNs here.
    log.info(f"[notify:{channel}] {message}")
    note = Notification(reminder_id=reminder_id,
                        channel=channel, result="success")
    db.add(note)
    db.commit()
    db.refresh(note)
    return note
