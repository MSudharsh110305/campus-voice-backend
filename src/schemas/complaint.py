"""
Pydantic schemas for Complaint endpoints.
"""

from pydantic import BaseModel, Field, field_validator
from typing import Optional, List
from datetime import datetime
from uuid import UUID
from src.config.constants import ComplaintStatus, PriorityLevel, VisibilityLevel


class ComplaintCreate(BaseModel):
    """Schema for creating a complaint"""
    
    category_id: int = Field(
        ...,
        gt=0,
        description="Complaint category ID",
        examples=[1]
    )
    original_text: str = Field(
        ...,
        min_length=10,
        max_length=2000,
        description="Original complaint text",
        examples=["The hostel room fan is not working for the past 3 days..."]
    )
    visibility: Optional[VisibilityLevel] = Field(
        default="Public",
        description="Complaint visibility level"
    )
    
    @field_validator('original_text')
    @classmethod
    def validate_text(cls, v: str) -> str:
        """Validate complaint text"""
        v = v.strip()
        if len(v) < 10:
            raise ValueError("Complaint must be at least 10 characters")
        if v.isupper():
            raise ValueError("Please avoid writing in all caps")
        return v
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "category_id": 1,
                "original_text": "The hostel room fan is not working for the past 3 days. It's very hot and difficult to sleep.",
                "visibility": "Public"
            }
        }
    }


class ComplaintUpdate(BaseModel):
    """Schema for updating complaint (by authority)"""
    
    status: ComplaintStatus = Field(
        ...,
        description="New status"
    )
    reason: Optional[str] = Field(
        None,
        max_length=500,
        description="Reason for status change"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "In Progress",
                "reason": "Forwarded to maintenance team"
            }
        }
    }


class ComplaintResponse(BaseModel):
    """Schema for complaint response (basic)"""
    
    id: UUID
    category_id: int
    category_name: Optional[str] = None
    original_text: str
    rephrased_text: Optional[str] = None
    visibility: str
    upvotes: int
    downvotes: int
    priority: str
    priority_score: float
    status: str
    assigned_authority_name: Optional[str] = None
    is_marked_as_spam: bool
    image_url: Optional[str] = None
    image_verified: bool
    submitted_at: datetime
    updated_at: datetime
    resolved_at: Optional[datetime] = None
    
    # Only for student's own complaints or admin
    student_roll_no: Optional[str] = None
    student_name: Optional[str] = None
    
    model_config = {
        "from_attributes": True,
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",
                "category_id": 1,
                "category_name": "Hostel",
                "original_text": "Room fan not working",
                "rephrased_text": "Issue: The ceiling fan in my hostel room has stopped functioning...",
                "visibility": "Public",
                "upvotes": 5,
                "downvotes": 0,
                "priority": "Medium",
                "priority_score": 50.5,
                "status": "In Progress",
                "assigned_authority_name": "Hostel Warden",
                "is_marked_as_spam": False,
                "image_url": None,
                "image_verified": False,
                "submitted_at": "2024-01-27T10:00:00",
                "updated_at": "2024-01-27T12:00:00",
                "resolved_at": None
            }
        }
    }


class ComplaintDetailResponse(ComplaintResponse):
    """Schema for detailed complaint response (with status history)"""
    
    student_department: Optional[str] = None
    student_gender: Optional[str] = None
    student_stay_type: Optional[str] = None
    complaint_department_id: Optional[int] = None
    is_cross_department: bool = False
    status_updates: Optional[List[dict]] = []
    vote_count: int = 0
    
    model_config = {
        "from_attributes": True
    }


class ComplaintSubmitResponse(BaseModel):
    """Schema for complaint submission response"""
    
    id: UUID  # ✅ CHANGED: from "complaint_id" to "id" (more RESTful)
    status: str
    message: str
    rephrased_text: Optional[str] = None
    priority: str
    assigned_authority: Optional[str] = None
    image_required: bool = False
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "id": "123e4567-e89b-12d3-a456-426614174000",  # ✅ CHANGED
                "status": "Submitted",
                "message": "Your complaint has been submitted and assigned to the Hostel Warden",
                "rephrased_text": "Issue: The ceiling fan in my hostel room...",
                "priority": "Medium",
                "assigned_authority": "Hostel Warden",
                "image_required": False
            }
        }
    }


class ComplaintListResponse(BaseModel):
    """Schema for complaint list with pagination"""
    
    complaints: List[ComplaintResponse]
    total: int
    page: int
    page_size: int
    total_pages: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "complaints": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5
            }
        }
    }


class ComplaintFilter(BaseModel):
    """Schema for filtering complaints"""
    
    status: Optional[ComplaintStatus] = None
    priority: Optional[PriorityLevel] = None
    category_id: Optional[int] = None
    department_id: Optional[int] = None
    assigned_to_me: Optional[bool] = None
    date_from: Optional[datetime] = None
    date_to: Optional[datetime] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "Raised",
                "priority": "High",
                "category_id": 1
            }
        }
    }


class SpamFlag(BaseModel):
    """Schema for flagging complaint as spam"""
    
    reason: str = Field(
        ...,
        min_length=10,
        max_length=500,
        description="Reason for marking as spam"
    )
    is_permanent: bool = Field(
        default=False,
        description="Permanent ban or temporary"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "reason": "This complaint contains abusive language and is not a genuine issue",
                "is_permanent": False
            }
        }
    }


class ImageUploadResponse(BaseModel):
    """Schema for image upload response"""
    
    image_url: str
    verified: bool
    verification_status: str
    message: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "image_url": "/uploads/images/complaint_123_image.jpg",
                "verified": True,
                "verification_status": "Verified",
                "message": "Image uploaded and verified successfully"
            }
        }
    }


__all__ = [
    "ComplaintCreate",
    "ComplaintUpdate",
    "ComplaintResponse",
    "ComplaintDetailResponse",
    "ComplaintSubmitResponse",
    "ComplaintListResponse",
    "ComplaintFilter",
    "SpamFlag",
    "ImageUploadResponse",
]
