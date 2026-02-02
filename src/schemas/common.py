"""
Common Pydantic schemas used across the application.
"""

from pydantic import BaseModel, Field
from typing import Optional, Any, Dict, List, Generic, TypeVar
from datetime import datetime

T = TypeVar('T')


class SuccessResponse(BaseModel):
    """Generic success response"""
    
    success: bool = True
    message: str
    data: Optional[Any] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": True,
                "message": "Operation completed successfully",
                "data": None
            }
        }
    }


class ErrorResponse(BaseModel):
    """Generic error response"""
    
    success: bool = False
    error: str
    detail: Optional[str] = None
    error_code: Optional[str] = None
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success": False,
                "error": "Invalid credentials",
                "detail": "Email or password is incorrect",
                "error_code": "AUTH_FAILED",
                "timestamp": "2024-01-27T10:00:00"
            }
        }
    }


class PaginationParams(BaseModel):
    """Schema for pagination parameters"""
    
    page: int = Field(
        default=1,
        ge=1,
        description="Page number (starts at 1)"
    )
    page_size: int = Field(
        default=20,
        ge=1,
        le=100,
        description="Number of items per page"
    )
    
    @property
    def skip(self) -> int:
        """Calculate skip value for database query"""
        return (self.page - 1) * self.page_size
    
    @property
    def limit(self) -> int:
        """Get limit value for database query"""
        return self.page_size
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "page": 1,
                "page_size": 20
            }
        }
    }


class PaginatedResponse(BaseModel, Generic[T]):
    """Generic paginated response"""
    
    items: List[T]
    total: int
    page: int
    page_size: int
    total_pages: int
    has_next: bool
    has_previous: bool
    
    @classmethod
    def create(
        cls,
        items: List[T],
        total: int,
        page: int,
        page_size: int
    ) -> "PaginatedResponse[T]":
        """Create paginated response"""
        total_pages = (total + page_size - 1) // page_size
        return cls(
            items=items,
            total=total,
            page=page,
            page_size=page_size,
            total_pages=total_pages,
            has_next=page < total_pages,
            has_previous=page > 1
        )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "items": [],
                "total": 100,
                "page": 1,
                "page_size": 20,
                "total_pages": 5,
                "has_next": True,
                "has_previous": False
            }
        }
    }


class HealthCheckResponse(BaseModel):
    """Schema for health check response"""
    
    status: str
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    database: str
    version: str
    uptime_seconds: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "healthy",
                "timestamp": "2024-01-27T10:00:00",
                "database": "connected",
                "version": "1.0.0",
                "uptime_seconds": 3600.5
            }
        }
    }


class TokenResponse(BaseModel):
    """Schema for token response"""
    
    access_token: str
    token_type: str = "Bearer"
    expires_in: int
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "Bearer",
                "expires_in": 604800
            }
        }
    }


class SystemStats(BaseModel):
    """Schema for system-wide statistics"""
    
    total_students: int
    total_authorities: int
    total_complaints: int
    complaints_by_status: Dict[str, int]
    complaints_by_priority: Dict[str, int]
    complaints_by_category: Dict[str, int]
    avg_resolution_time_hours: Optional[float] = None
    spam_percentage: Optional[float] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_students": 1000,
                "total_authorities": 50,
                "total_complaints": 500,
                "complaints_by_status": {
                    "Raised": 50,
                    "In Progress": 100,
                    "Resolved": 300,
                    "Closed": 50
                },
                "complaints_by_priority": {
                    "Low": 100,
                    "Medium": 250,
                    "High": 100,
                    "Critical": 50
                },
                "complaints_by_category": {
                    "Hostel": 200,
                    "General": 150,
                    "Department": 100,
                    "Disciplinary Committee": 50
                },
                "avg_resolution_time_hours": 36.5,
                "spam_percentage": 2.5
            }
        }
    }


class MessageResponse(BaseModel):
    """Simple message response"""
    
    message: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Operation completed successfully"
            }
        }
    }


class ValidationError(BaseModel):
    """Schema for validation error details"""
    
    field: str
    message: str
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "field": "email",
                "message": "Invalid email format"
            }
        }
    }


class BulkOperationResponse(BaseModel):
    """Schema for bulk operation response"""
    
    success_count: int
    failure_count: int
    total: int
    errors: Optional[List[Dict[str, Any]]] = None
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "success_count": 8,
                "failure_count": 2,
                "total": 10,
                "errors": [
                    {"index": 3, "error": "Invalid data"},
                    {"index": 7, "error": "Duplicate entry"}
                ]
            }
        }
    }


__all__ = [
    "SuccessResponse",
    "ErrorResponse",
    "PaginationParams",
    "PaginatedResponse",
    "HealthCheckResponse",
    "TokenResponse",
    "SystemStats",
    "MessageResponse",
    "ValidationError",
    "BulkOperationResponse",
]
