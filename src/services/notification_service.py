"""
Notification service for creating and sending notifications.
"""

import logging
from typing import Optional
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Notification
from src.repositories.notification_repo import NotificationRepository

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for notification operations"""
    
    async def create_notification(
        self,
        db: AsyncSession,
        recipient_type: str,
        recipient_id: str,
        complaint_id: Optional[UUID],
        notification_type: str,
        message: str
    ) -> Notification:
        """
        Create a new notification.
        
        Args:
            db: Database session
            recipient_type: Student or Authority
            recipient_id: Recipient ID
            complaint_id: Optional complaint ID
            notification_type: Notification type
            message: Notification message
        
        Returns:
            Created notification
        """
        notification_repo = NotificationRepository(db)
        
        notification = await notification_repo.create(
            recipient_type=recipient_type,
            recipient_id=recipient_id,
            complaint_id=complaint_id,
            notification_type=notification_type,
            message=message
        )
        
        logger.info(f"Notification created for {recipient_type}:{recipient_id}")
        
        # TODO: Send real-time notification via WebSocket
        
        return notification
    
    async def mark_as_read(
        self,
        db: AsyncSession,
        notification_id: int
    ) -> bool:
        """
        Mark notification as read.
        
        Args:
            db: Database session
            notification_id: Notification ID
        
        Returns:
            True if successful
        """
        notification_repo = NotificationRepository(db)
        return await notification_repo.mark_as_read(notification_id)
    
    async def get_unread_count(
        self,
        db: AsyncSession,
        recipient_type: str,
        recipient_id: str
    ) -> int:
        """
        Get unread notification count.
        
        Args:
            db: Database session
            recipient_type: Student or Authority
            recipient_id: Recipient ID
        
        Returns:
            Unread count
        """
        notification_repo = NotificationRepository(db)
        return await notification_repo.count_unread(recipient_type, recipient_id)


# Create global instance
notification_service = NotificationService()

__all__ = ["NotificationService", "notification_service"]
