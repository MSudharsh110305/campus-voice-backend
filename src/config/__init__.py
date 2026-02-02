"""
Configuration module for CampusVoice.
"""

from .settings import settings, Settings
from .constants import (
    DEPARTMENTS,
    CATEGORIES,
    AUTHORITY_LEVELS,
    PRIORITY_SCORES,
    ComplaintStatus,
    PriorityLevel,
    AuthorityType,
    CategoryName,
    DepartmentCode,
)

__all__ = [
    "settings",
    "Settings",
    "DEPARTMENTS",
    "CATEGORIES",
    "AUTHORITY_LEVELS",
    "PRIORITY_SCORES",
    "ComplaintStatus",
    "PriorityLevel",
    "AuthorityType",
    "CategoryName",
    "DepartmentCode",
]
