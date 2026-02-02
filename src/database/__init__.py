"""
Database package initialization.
Exports all models and connection utilities.
"""

from .connection import (
    engine,
    AsyncSessionLocal,
    get_db,
    create_all_tables,
    drop_all_tables,
    init_db,
    health_check,
    get_db_info,
    close_db,
)

from .models import (
    Base,
    Student,
    Department,
    ComplaintCategory,
    Authority,
    Complaint,
    Vote,
    StatusUpdate,
    AuthorityRoutingRule,
    ImageVerificationLog,
    SpamBlacklist,
    LLMProcessingLog,
    Notification,
    Comment,
    AdminAuditLog,
)

__all__ = [
    # Connection
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "create_all_tables",
    "drop_all_tables",
    "init_db",
    "health_check",
    "get_db_info",
    "close_db",
    
    # Models
    "Base",
    "Student",
    "Department",
    "ComplaintCategory",
    "Authority",
    "Complaint",
    "Vote",
    "StatusUpdate",
    "AuthorityRoutingRule",
    "ImageVerificationLog",
    "SpamBlacklist",
    "LLMProcessingLog",
    "Notification",
    "Comment",
    "AdminAuditLog",
]
