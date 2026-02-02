"""
Pydantic schemas for Authority endpoints.
"""

from pydantic import BaseModel, EmailStr, Field, field_validator, ValidationInfo
from typing import Optional, List
from datetime import datetime
from src.config.constants import (
    AuthorityType,
    AnnouncementCategory,
    AnnouncementPriority,
    VisibilityLevel
)


class AuthorityLogin(BaseModel):
    """Schema for authority login"""
    
    email: EmailStr = Field(
        ...,
        description="Authority email address"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Password"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "email": "warden@college.edu",
                "password": "SecurePass123!"
            }
        }
    }


class AuthorityCreate(BaseModel):
    """Schema for creating authority (admin only)"""
    
    name: str = Field(..., min_length=2, max_length=255)
    email: EmailStr
    password: str = Field(..., min_length=8)
    phone: Optional[str] = Field(
        None,
        pattern=r'^[6-9]\d{9}$',
        description="Indian mobile number (10 digits starting with 6-9)"
    )
    authority_type: AuthorityType
    department_id: Optional[int] = Field(None, gt=0)
    designation: Optional[str] = Field(None, max_length=255)
    authority_level: int = Field(..., ge=1, le=100)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Dr. John Smith",
                "email": "john.smith@college.edu",
                "password": "SecurePass123!",
                "phone": "9876543210",
                "authority_type": "Warden",
                "department_id": None,
                "designation": "Chief Warden",
                "authority_level": 5
            }
        }
    }


class AuthorityProfile(BaseModel):
    """Schema for authority profile"""
    
    id: int
    name: str
    email: str
    phone: Optional[str] = None
    authority_type: str
    department_id: Optional[int] = None
    department_name: Optional[str] = None
    designation: Optional[str] = None
    authority_level: int
    is_active: bool
    created_at: datetime
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Dr. John Smith",
                "email": "john.smith@college.edu",
                "phone": "9876543210",
                "authority_type": "Warden",
                "department_id": None,
                "department_name": None,
                "designation": "Chief Warden",
                "authority_level": 5,
                "is_active": True,
                "created_at": "2025-08-15T09:00:00"
            }
        }
    }


class AuthorityResponse(BaseModel):
    """Schema for authority login response"""
    
    id: int
    name: str
    email: str
    authority_type: str
    department_id: Optional[int] = None
    designation: Optional[str] = None
    token: str
    token_type: str = "Bearer"
    expires_in: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": 1,
                "name": "Dr. John Smith",
                "email": "john.smith@college.edu",
                "authority_type": "Warden",
                "department_id": None,
                "designation": "Chief Warden",
                "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 604800
            }
        }
    }


class AuthorityStats(BaseModel):
    """Schema for authority statistics"""
    
    total_assigned: int
    pending: int
    in_progress: int
    resolved: int
    closed: int
    spam_flagged: int
    avg_resolution_time_hours: Optional[float] = None
    performance_rating: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_assigned": 50,
                "pending": 5,
                "in_progress": 10,
                "resolved": 30,
                "closed": 5,
                "spam_flagged": 2,
                "avg_resolution_time_hours": 24.5,
                "performance_rating": 4.5
            }
        }
    }


class AuthorityDashboard(BaseModel):
    """Schema for authority dashboard data"""
    
    profile: AuthorityProfile
    stats: AuthorityStats
    recent_complaints: List[dict]
    urgent_complaints: List[dict]
    unread_notifications: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "profile": {},
                "stats": {},
                "recent_complaints": [],
                "urgent_complaints": [],
                "unread_notifications": 3
            }
        }
    }


class AuthorityProfileUpdate(BaseModel):
    """Schema for updating authority profile (renamed from AuthorityUpdate for clarity)"""
    
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(
        None,
        pattern=r'^[6-9]\d{9}$',
        description="Indian mobile number (10 digits starting with 6-9)"
    )
    designation: Optional[str] = Field(None, max_length=255)
    is_active: Optional[bool] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "name": "Dr. John Smith",
                "phone": "9876543210",
                "designation": "Senior Warden"
            }
        }
    }


class AuthorityListResponse(BaseModel):
    """Schema for authority list"""
    
    authorities: List[AuthorityProfile]
    total: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "authorities": [],
                "total": 10
            }
        }
    }


# ==================== AUTHORITY ANNOUNCEMENTS/UPDATES ====================


class AuthorityAnnouncementCreate(BaseModel):
    """Schema for creating authority announcement/update"""
    
    title: str = Field(
        ...,
        min_length=5,
        max_length=255,
        description="Announcement title",
        examples=["Important: Hostel Maintenance Schedule"]
    )
    content: str = Field(
        ...,
        min_length=10,
        max_length=5000,
        description="Announcement content/message",
        examples=["The hostel will undergo routine maintenance from Feb 10-12. Please cooperate."]
    )
    category: AnnouncementCategory = Field(
        ...,
        description="Announcement category: Announcement, Notice, Alert, Maintenance, Event",
        examples=["Maintenance"]
    )
    priority: AnnouncementPriority = Field(
        default="Medium",
        description="Priority level: Low, Medium, High, Critical",
        examples=["High"]
    )
    visibility: VisibilityLevel = Field(
        default="All Students",
        description="Who can see this: All Students, Department Only, Hostel Only, Public",
        examples=["Hostel Only"]
    )
    expires_at: Optional[datetime] = Field(
        None,
        description="When this announcement expires (optional)",
        examples=["2026-02-12T23:59:59"]
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: str) -> str:
        """Validate title"""
        v = v.strip()
        if not v:
            raise ValueError("Title cannot be empty")
        if v.isupper():
            raise ValueError("Please avoid writing title in all caps")
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: str) -> str:
        """Validate content"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Content must be at least 10 characters")
        return v
    
    @field_validator('expires_at')
    @classmethod
    def validate_expires_at(cls, v: Optional[datetime]) -> Optional[datetime]:
        """Validate expiry date is in future"""
        if v is not None:
            if v <= datetime.utcnow():
                raise ValueError("Expiry date must be in the future")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Important: Hostel Maintenance Schedule",
                "content": "The hostel will undergo routine maintenance from Feb 10-12, 2026. Water supply will be affected from 9 AM to 5 PM. Please store water in advance. We apologize for the inconvenience.",
                "category": "Maintenance",
                "priority": "High",
                "visibility": "Hostel Only",
                "expires_at": "2026-02-12T23:59:59"
            }
        }
    }


class AuthorityAnnouncementUpdate(BaseModel):
    """Schema for updating authority announcement"""
    
    title: Optional[str] = Field(
        None,
        min_length=5,
        max_length=255,
        description="Updated title"
    )
    content: Optional[str] = Field(
        None,
        min_length=10,
        max_length=5000,
        description="Updated content"
    )
    category: Optional[AnnouncementCategory] = None
    priority: Optional[AnnouncementPriority] = None
    visibility: Optional[VisibilityLevel] = None
    expires_at: Optional[datetime] = None
    is_active: Optional[bool] = Field(
        None,
        description="Set to False to hide/archive the announcement"
    )
    
    @field_validator('title')
    @classmethod
    def validate_title(cls, v: Optional[str]) -> Optional[str]:
        """Validate title"""
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("Title cannot be empty")
            if v.isupper():
                raise ValueError("Please avoid writing title in all caps")
        return v
    
    @field_validator('content')
    @classmethod
    def validate_content(cls, v: Optional[str]) -> Optional[str]:
        """Validate content"""
        if v is not None:
            v = v.strip()
            if len(v) < 10:
                raise ValueError("Content must be at least 10 characters")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "title": "Updated: Hostel Maintenance Postponed",
                "content": "The maintenance has been postponed to Feb 15-17.",
                "priority": "Medium",
                "expires_at": "2026-02-17T23:59:59"
            }
        }
    }


class AuthorityAnnouncementResponse(BaseModel):
    """Schema for authority announcement response"""
    
    id: int
    authority_id: int
    authority_name: Optional[str] = None
    authority_type: Optional[str] = None
    title: str
    content: str
    category: str
    priority: str
    visibility: str
    views_count: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    expires_at: Optional[datetime] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": 1,
                "authority_id": 5,
                "authority_name": "Dr. John Smith",
                "authority_type": "Warden",
                "title": "Important: Hostel Maintenance Schedule",
                "content": "The hostel will undergo routine maintenance...",
                "category": "Maintenance",
                "priority": "High",
                "visibility": "Hostel Only",
                "views_count": 150,
                "is_active": True,
                "created_at": "2026-02-05T10:00:00",
                "updated_at": "2026-02-05T10:00:00",
                "expires_at": "2026-02-12T23:59:59"
            }
        }
    }


class AuthorityAnnouncementListResponse(BaseModel):
    """Schema for authority announcement list with pagination"""
    
    announcements: List[AuthorityAnnouncementResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    active_count: int
    expired_count: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "announcements": [],
                "total": 25,
                "page": 1,
                "page_size": 10,
                "total_pages": 3,
                "active_count": 20,
                "expired_count": 5
            }
        }
    }


__all__ = [
    # Authority Management
    "AuthorityLogin",
    "AuthorityCreate",
    "AuthorityProfile",
    "AuthorityResponse",
    "AuthorityStats",
    "AuthorityDashboard",
    "AuthorityProfileUpdate",  # ✅ RENAMED from AuthorityUpdate
    "AuthorityListResponse",
    
    # Authority Announcements (NEW)
    "AuthorityAnnouncementCreate",
    "AuthorityAnnouncementUpdate",
    "AuthorityAnnouncementResponse",
    "AuthorityAnnouncementListResponse",
]
