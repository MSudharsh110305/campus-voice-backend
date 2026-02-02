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
    seed_initial_data,  # ✅ NEW: Export for testing/manual seeding
    health_check,
    get_db_info,
    close_db,
    execute_in_transaction,  # ✅ NEW: Export transaction helper
)

from .models import (
    Base,
    Student,
    Department,
    ComplaintCategory,
    Authority,
    Complaint,
    AuthorityUpdate,  # ✅ NEW: Authority updates/announcements model
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
    "seed_initial_data",  # ✅ NEW
    "health_check",
    "get_db_info",
    "close_db",
    "execute_in_transaction",  # ✅ NEW
    
    # Models
    "Base",
    "Student",
    "Department",
    "ComplaintCategory",
    "Authority",
    "Complaint",
    "AuthorityUpdate",  # ✅ NEW
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
