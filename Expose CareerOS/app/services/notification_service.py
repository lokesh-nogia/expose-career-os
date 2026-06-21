from sqlalchemy.orm import Session
from datetime import datetime
from typing import List, Optional
from app.models.domain import Notification

def create_notification(db: Session, n_type: str, message: str) -> Notification:
    """Creates a new workspace notification."""
    notif = Notification(
        type=n_type,
        message=message,
        created_at=datetime.utcnow(),
        read=False
    )
    db.add(notif)
    db.commit()
    db.refresh(notif)
    return notif

def list_notifications(db: Session, unread_only: bool = False, limit: int = 10) -> List[Notification]:
    """Retrieves list of recent notifications."""
    query = db.query(Notification)
    if unread_only:
        query = query.filter(Notification.read == False)
    return query.order_by(Notification.created_at.desc()).limit(limit).all()

def mark_as_read(db: Session, notification_id: int) -> bool:
    """Marks a single notification as read."""
    notif = db.query(Notification).filter(Notification.id == notification_id).first()
    if notif:
        notif.read = True
        db.commit()
        return True
    return False

def mark_all_as_read(db: Session) -> None:
    """Marks all notifications as read."""
    db.query(Notification).filter(Notification.read == False).update({"read": True})
    db.commit()
