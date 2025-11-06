"""Pydantic schemas for notifications."""
from __future__ import annotations
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from app.models.notification import NotificationType, NotificationPriority


class NotificationResponse(BaseModel):
    """Notification details."""
    id: str
    user_id: int
    type: NotificationType
    priority: NotificationPriority
    title: str
    message: str
    related_entity_type: Optional[str]
    related_entity_id: Optional[str]
    is_read: bool
    read_at: Optional[datetime]
    action_url: Optional[str]
    action_label: Optional[str]
    notification_metadata: Optional[dict]
    created_at: datetime
    expires_at: Optional[datetime]

    class Config:
        from_attributes = True


class NotificationListResponse(BaseModel):
    """Paginated notifications list."""
    notifications: list[NotificationResponse]
    total: int
    unread_count: int


class MarkAsReadRequest(BaseModel):
    """Mark notification(s) as read."""
    notification_ids: list[str]


__all__ = [
    "NotificationResponse",
    "NotificationListResponse",
    "MarkAsReadRequest",
]

