"""Notifications API."""
from datetime import datetime
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.notification import Notification, NotificationType
from app.schemas.notification import (
    NotificationResponse,
    NotificationListResponse,
    MarkAsReadRequest,
)

router = APIRouter()


@router.get("/notifications", response_model=NotificationListResponse)
def list_notifications(
    unread_only: bool = Query(False),
    notification_type: NotificationType | None = Query(None, alias="type"),
    limit: int = Query(50, ge=1, le=100),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user's notifications.
    
    **Filters:**
    - unread_only: Show only unread notifications
    - type: Filter by notification type
    
    **Returns:** Paginated list with unread count.
    """
    query = db.query(Notification).filter(Notification.user_id == current_user.id)
    
    if unread_only:
        query = query.filter(Notification.is_read == False)
    if notification_type:
        query = query.filter(Notification.type == notification_type)
    
    total = query.count()
    unread_count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    
    notifications = query.order_by(Notification.created_at.desc()).offset(offset).limit(limit).all()
    
    return NotificationListResponse(
        notifications=[NotificationResponse.from_orm(n) for n in notifications],
        total=total,
        unread_count=unread_count
    )


@router.post("/notifications/mark-read", status_code=status.HTTP_204_NO_CONTENT)
def mark_notifications_as_read(
    payload: MarkAsReadRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Mark notifications as read.
    
    **Use case:** User views notification(s).
    """
    notifications = (
        db.query(Notification)
        .filter(
            Notification.id.in_(payload.notification_ids),
            Notification.user_id == current_user.id,
            Notification.is_read == False
        )
        .all()
    )
    
    for notification in notifications:
        notification.is_read = True
        notification.read_at = datetime.utcnow()
    
    db.commit()
    return


@router.delete("/notifications/{notification_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_notification(
    notification_id: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete notification.
    
    **Use case:** User dismisses notification.
    """
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id
        )
        .first()
    )
    
    if notification:
        db.delete(notification)
        db.commit()
    
    return


@router.get("/notifications/unread/count")
def get_unread_count(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get unread notifications count.
    
    **Use case:** Display badge count in UI.
    """
    count = (
        db.query(Notification)
        .filter(Notification.user_id == current_user.id, Notification.is_read == False)
        .count()
    )
    
    return {"unread_count": count}

