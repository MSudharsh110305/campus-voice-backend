"""
Pydantic schemas for Authority endpoints.
"""

from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from src.config.constants import AuthorityType


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
    phone: Optional[str] = Field(None, pattern=r'^[6-9]\d{9}$')
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
                "created_at": "2024-01-01T00:00:00"
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


class AuthorityUpdate(BaseModel):
    """Schema for updating authority profile"""
    
    name: Optional[str] = Field(None, min_length=2, max_length=255)
    phone: Optional[str] = Field(None, pattern=r'^[6-9]\d{9}$')
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


__all__ = [
    "AuthorityLogin",
    "AuthorityCreate",
    "AuthorityProfile",
    "AuthorityResponse",
    "AuthorityStats",
    "AuthorityDashboard",
    "AuthorityUpdate",
    "AuthorityListResponse",
]
