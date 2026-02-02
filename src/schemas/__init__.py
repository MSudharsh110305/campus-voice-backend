"""
Pydantic schemas package initialization.
All validation models for API requests and responses.
"""

from .student import (
    StudentRegister,
    StudentLogin,
    StudentProfile,
    StudentProfileUpdate,
    StudentResponse,
    StudentStats,
    PasswordChange,
    EmailVerification,
)

from .complaint import (
    ComplaintCreate,
    ComplaintUpdate,
    ComplaintResponse,
    ComplaintDetailResponse,
    ComplaintSubmitResponse,
    ComplaintListResponse,
    ComplaintFilter,
    SpamFlag,
    ImageUploadResponse,
)

from .authority import (
    AuthorityLogin,
    AuthorityCreate,
    AuthorityProfile,
    AuthorityResponse,
    AuthorityStats,
    AuthorityDashboard,
    AuthorityUpdate,
    AuthorityListResponse,
)

from .vote import (
    VoteCreate,
    VoteResponse,
    VoteStats,
    VoteDeleteResponse,
)

from .notification import (
    NotificationCreate,
    NotificationResponse,
    NotificationListResponse,
    NotificationMarkRead,
    NotificationUnreadCount,
)

from .common import (
    SuccessResponse,
    ErrorResponse,
    PaginationParams,
    PaginatedResponse,
    HealthCheckResponse,
    TokenResponse,
    SystemStats,
    MessageResponse,
    ValidationError,
    BulkOperationResponse,
)

__all__ = [
    # Student
    "StudentRegister",
    "StudentLogin",
    "StudentProfile",
    "StudentProfileUpdate",
    "StudentResponse",
    "StudentStats",
    "PasswordChange",
    "EmailVerification",
    
    # Complaint
    "ComplaintCreate",
    "ComplaintUpdate",
    "ComplaintResponse",
    "ComplaintDetailResponse",
    "ComplaintSubmitResponse",
    "ComplaintListResponse",
    "ComplaintFilter",
    "SpamFlag",
    "ImageUploadResponse",
    
    # Authority
    "AuthorityLogin",
    "AuthorityCreate",
    "AuthorityProfile",
    "AuthorityResponse",
    "AuthorityStats",
    "AuthorityDashboard",
    "AuthorityUpdate",
    "AuthorityListResponse",
    
    # Vote
    "VoteCreate",
    "VoteResponse",
    "VoteStats",
    "VoteDeleteResponse",
    
    # Notification
    "NotificationCreate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationMarkRead",
    "NotificationUnreadCount",
    
    # Common
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
