"""
Pydantic schemas for Notification endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from src.config.constants import NotificationType


class NotificationCreate(BaseModel):
    """Schema for creating a notification (internal use)"""
    
    recipient_type: str  # Student, Authority
    recipient_id: str  # roll_no or authority_id
    complaint_id: Optional[UUID] = None
    notification_type: NotificationType
    message: str = Field(..., min_length=1, max_length=500)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "recipient_type": "Student",
                "recipient_id": "21CSE001",
                "complaint_id": "123e4567-e89b-12d3-a456-426614174000",
                "notification_type": "status_update",
                "message": "Your complaint has been updated to 'In Progress'"
            }
        }
    }


class NotificationResponse(BaseModel):
    """Schema for notification response"""
    
    id: int
    recipient_type: str
    complaint_id: Optional[UUID] = None
    notification_type: str
    message: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime] = None
    
    # Additional complaint info (optional)
    complaint_title: Optional[str] = None
    complaint_status: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "recipient_type": "Student",
                "complaint_id": "123e4567-e89b-12d3-a456-426614174000",
                "notification_type": "status_update",
                "message": "Your complaint has been updated to 'In Progress'",
                "is_read": False,
                "created_at": "2024-01-27T10:00:00",
                "read_at": None,
                "complaint_title": "Room fan not working",
                "complaint_status": "In Progress"
            }
        }
    }


class NotificationListResponse(BaseModel):
    """Schema for notification list"""
    
    notifications: List[NotificationResponse]
    total: int
    unread_count: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "notifications": [],
                "total": 10,
                "unread_count": 3
            }
        }
    }


class NotificationMarkRead(BaseModel):
    """Schema for marking notifications as read"""
    
    notification_ids: List[int] = Field(
        ...,
        min_length=1,
        description="List of notification IDs to mark as read"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "notification_ids": [1, 2, 3]
            }
        }
    }


class NotificationUnreadCount(BaseModel):
    """Schema for unread notification count"""
    
    unread_count: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "unread_count": 5
            }
        }
    }


__all__ = [
    "NotificationCreate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationMarkRead",
    "NotificationUnreadCount",
]
