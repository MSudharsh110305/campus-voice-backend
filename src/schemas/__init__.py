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
    CommentCreate,
    CommentResponse,
    CommentListResponse,
)

from .authority import (
    AuthorityLogin,
    AuthorityCreate,
    AuthorityProfile,
    AuthorityResponse,
    AuthorityStats,
    AuthorityDashboard,
    AuthorityProfileUpdate,
    AuthorityListResponse,
    AuthorityAnnouncementCreate,
    AuthorityAnnouncementUpdate,
    AuthorityAnnouncementResponse,
    AuthorityAnnouncementListResponse,
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
    DateRangeFilter,
)


__all__ = [
    # Student schemas
    "StudentRegister",
    "StudentLogin",
    "StudentProfile",
    "StudentProfileUpdate",
    "StudentResponse",
    "StudentStats",
    "PasswordChange",
    "EmailVerification",
    
    # Complaint schemas
    "ComplaintCreate",
    "ComplaintUpdate",
    "ComplaintResponse",
    "ComplaintDetailResponse",
    "ComplaintSubmitResponse",
    "ComplaintListResponse",
    "ComplaintFilter",
    "SpamFlag",
    "ImageUploadResponse",
    "CommentCreate",
    "CommentResponse",
    "CommentListResponse",
    
    # Authority schemas
    "AuthorityLogin",
    "AuthorityCreate",
    "AuthorityProfile",
    "AuthorityResponse",
    "AuthorityStats",
    "AuthorityDashboard",
    "AuthorityProfileUpdate",
    "AuthorityListResponse",
    "AuthorityAnnouncementCreate",
    "AuthorityAnnouncementUpdate",
    "AuthorityAnnouncementResponse",
    "AuthorityAnnouncementListResponse",
    
    # Vote schemas
    "VoteCreate",
    "VoteResponse",
    "VoteStats",
    "VoteDeleteResponse",
    
    # Notification schemas
    "NotificationCreate",
    "NotificationResponse",
    "NotificationListResponse",
    "NotificationMarkRead",
    "NotificationUnreadCount",
    
    # Common schemas
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
    "DateRangeFilter",
]
