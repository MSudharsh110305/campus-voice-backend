"""
Fixed constants for CampusVoice application.
Department codes, categories, authority levels, status transitions, etc.
"""

from typing import Dict, List
from enum import Enum
import re


# ==================== DEPARTMENTS ====================

class DepartmentCode(str, Enum):
    """Department code enums"""
    CSE = "CSE"
    ECE = "ECE"
    MECH = "MECH"
    CIVIL = "CIVIL"
    EEE = "EEE"
    IT = "IT"
    BIO = "BIO"
    AERO = "AERO"
    RAA = "RAA"  # Robotics and Automation
    EIE = "EIE"  # Electronics & Instrumentation Engineering
    MBA = "MBA"  # Management Studies
    AIDS = "AIDS"  # Artificial Intelligence and Data Science
    MTECH_CSE = "MTECH_CSE"  # M.Tech in Computer Science and Engineering


DEPARTMENTS: List[Dict[str, str]] = [
    {
        "code": "CSE",
        "name": "Computer Science & Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "ECE",
        "name": "Electronics & Communication Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "RAA",
        "name": "Robotics and Automation",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "MECH",
        "name": "Mechanical Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "EEE",
        "name": "Electrical & Electronics Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "EIE",
        "name": "Electronics & Instrumentation Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "BIO",
        "name": "Biomedical Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "AERO",
        "name": "Aeronautical Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "CIVIL",
        "name": "Civil Engineering",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "IT",
        "name": "Information Technology",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "MBA",
        "name": "Management Studies",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "AIDS",
        "name": "Artificial Intelligence and Data Science",
        "hod_name": None,
        "hod_email": None,
    },
    {
        "code": "MTECH_CSE",
        "name": "M.Tech in Computer Science and Engineering",
        "hod_name": None,
        "hod_email": None,
    },
]
# ==================== COMPLAINT CATEGORIES ====================

class CategoryName(str, Enum):
    """Complaint category enums"""
    HOSTEL = "Hostel"
    GENERAL = "General"
    DEPARTMENT = "Department"
    DISCIPLINARY = "Disciplinary Committee"


CATEGORIES: List[Dict[str, any]] = [
    {
        "name": "Hostel",
        "description": "Hostel facilities, cleanliness, room issues, mess complaints, amenities",
        "keywords": ["room", "hostel", "warden", "bed", "hall", "mess", "food", "water", "bathroom", "toilet", "shower", "ac", "fan", "electricity"],
    },
    {
        "name": "General",
        "description": "Canteen, library, playground, common areas, campus facilities",
        "keywords": ["canteen", "library", "playground", "gate", "parking", "wifi", "common area", "ground", "gym", "cafeteria", "auditorium"],
    },
    {
        "name": "Department",
        "description": "Academic issues, lab facilities, department infrastructure, faculty concerns",
        "keywords": ["lab", "class", "classroom", "exam", "faculty", "professor", "teacher", "assignment", "project", "department", "lecture", "practical"],
    },
    {
        "name": "Disciplinary Committee",
        "description": "Ragging, harassment, bullying, serious violations, safety concerns",
        "keywords": ["ragging", "harassment", "bully", "bullying", "fight", "safety", "threat", "violence", "abuse", "assault", "misbehavior"],
    },
]


# ==================== AUTHORITY TYPES ====================

class AuthorityType(str, Enum):
    """Authority type enums"""
    ADMIN = "Admin"
    ADMIN_OFFICER = "Admin Officer"
    WARDEN = "Warden"
    DEPUTY_WARDEN = "Deputy Warden"
    SENIOR_DEPUTY_WARDEN = "Senior Deputy Warden"
    HOD = "HOD"
    DISCIPLINARY_COMMITTEE = "Disciplinary Committee"


# Authority Hierarchy Levels (higher = more authority)
AUTHORITY_LEVELS: Dict[str, int] = {
    "Admin": 100,
    "Admin Officer": 50,
    "Disciplinary Committee": 20,
    "Senior Deputy Warden": 15,
    "Deputy Warden": 10,
    "HOD": 8,
    "Warden": 5,
}

# Reverse mapping: level to authority type
LEVEL_TO_AUTHORITY: Dict[int, str] = {
    v: k for k, v in AUTHORITY_LEVELS.items()
}


# ==================== COMPLAINT STATUS ====================

class ComplaintStatus(str, Enum):
    """Complaint status enums"""
    RAISED = "Raised"
    IN_PROGRESS = "In Progress"
    RESOLVED = "Resolved"
    CLOSED = "Closed"
    SPAM = "Spam"


VALID_STATUS_TRANSITIONS: Dict[str, List[str]] = {
    "Raised": ["In Progress", "Spam", "Closed"],
    "In Progress": ["Resolved", "Raised", "Closed"],
    "Resolved": ["Closed", "Raised"],
    "Closed": [],  # Terminal state
    "Spam": ["Closed"],  # Can only close spam
}


# ==================== PRIORITY LEVELS ====================

class PriorityLevel(str, Enum):
    """Priority level enums"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    CRITICAL = "Critical"


# Base priority scores (will be overridden by settings)
PRIORITY_SCORES: Dict[str, float] = {
    "Low": 10.0,
    "Medium": 50.0,
    "High": 100.0,
    "Critical": 200.0,
}

# Vote impact multiplier (overridden by settings)
VOTE_IMPACT_MULTIPLIER: float = 2.0

# Priority thresholds for auto-escalation
PRIORITY_AUTO_ESCALATE_THRESHOLD: float = 150.0


# ==================== VISIBILITY LEVELS ====================

class VisibilityLevel(str, Enum):
    """Complaint visibility enums"""
    PRIVATE = "Private"
    DEPARTMENT = "Department"
    PUBLIC = "Public"


# ==================== STUDENT ENUMS ====================

class Gender(str, Enum):
    """Gender enums"""
    MALE = "Male"
    FEMALE = "Female"
    OTHER = "Other"


class StayType(str, Enum):
    """Stay type enums"""
    HOSTEL = "Hostel"
    DAY_SCHOLAR = "Day Scholar"


# ✅ NEW: Student Year Enum
class StudentYear(str, Enum):
    """Student year/grade enums"""
    FIRST = "1st Year"
    SECOND = "2nd Year"
    THIRD = "3rd Year"
    FOURTH = "4th Year"


# Valid years list for validation
VALID_YEARS: List[str] = ["1st Year", "2nd Year", "3rd Year", "4th Year"]


# ==================== VOTE TYPES ====================

class VoteType(str, Enum):
    """Vote type enums"""
    UPVOTE = "Upvote"
    DOWNVOTE = "Downvote"


# ==================== NOTIFICATION TYPES ====================

class NotificationType(str, Enum):
    """Notification type enums"""
    STATUS_UPDATE = "status_update"
    COMPLAINT_ASSIGNED = "complaint_assigned"
    ESCALATION = "escalation"
    SPAM_ALERT = "spam_alert"
    COMMENT_ADDED = "comment_added"
    VOTE_MILESTONE = "vote_milestone"
    COMPLAINT_RESOLVED = "complaint_resolved"
    COMPLAINT_CLOSED = "complaint_closed"
    # ✅ NEW: Authority update notifications
    AUTHORITY_UPDATE_POSTED = "authority_update_posted"
    URGENT_UPDATE = "urgent_update"


# ==================== LLM OPERATION TYPES ====================

class LLMOperationType(str, Enum):
    """LLM operation type enums"""
    CATEGORIZATION = "categorization"
    REPHRASING = "rephrasing"
    IMAGE_VERIFICATION = "image_verification"
    SPAM_DETECTION = "spam_detection"


# ==================== IMAGE VERIFICATION STATUS ====================

class ImageVerificationStatus(str, Enum):
    """Image verification status enums"""
    PENDING = "Pending"
    VERIFIED = "Verified"
    REJECTED = "Rejected"


# ==================== AUTHORITY UPDATES (NEW FEATURE) ====================

class UpdatePriority(str, Enum):
    """Authority update priority levels"""
    LOW = "Low"
    MEDIUM = "Medium"
    HIGH = "High"
    URGENT = "Urgent"


class UpdateVisibility(str, Enum):
    """Authority update visibility levels"""
    DEPARTMENT = "Department"  # Only visible to specific department
    YEAR = "Year"              # Only visible to specific year
    HOSTEL = "Hostel"          # Only visible to hostel students
    DAY_SCHOLAR = "Day Scholar"  # Only visible to day scholars
    ALL_STUDENTS = "All Students"  # Visible to everyone


class UpdateCategory(str, Enum):
    """Authority update categories"""
    ANNOUNCEMENT = "Announcement"
    POLICY_CHANGE = "Policy Change"
    EVENT = "Event"
    MAINTENANCE = "Maintenance"
    EMERGENCY = "Emergency"
    GENERAL = "General"


# Authority update constants
MAX_UPDATE_LENGTH: int = 5000  # Characters
MIN_UPDATE_LENGTH: int = 10    # Characters
UPDATE_EXPIRY_DAYS: int = 30   # Auto-hide after 30 days


# ==================== ROUTING RULES ====================

# Default routing by category
DEFAULT_CATEGORY_ROUTING: Dict[str, str] = {
    "Hostel": "Warden",
    "General": "Admin Officer",
    "Department": "HOD",  # Dynamic based on student department
    "Disciplinary Committee": "Disciplinary Committee",
}

# Cross-department complaint routing
CROSS_DEPARTMENT_AUTHORITY: str = "Admin Officer"

# Authority escalation rules (if complaint is against assigned authority)
ESCALATION_RULES: Dict[str, str] = {
    "Warden": "Deputy Warden",
    "Deputy Warden": "Senior Deputy Warden",
    "Senior Deputy Warden": "Admin Officer",
    "HOD": "Admin Officer",
    "Admin Officer": "Admin",
    "Disciplinary Committee": "Admin",
    "Admin": "Admin",  # No further escalation
}


# ==================== RATE LIMITING ====================

# Rate limit keys (templates)
RATE_LIMIT_KEYS = {
    "student_complaints": "student:{roll_no}:complaints",
    "student_votes": "student:{roll_no}:votes",
    "student_api": "student:{roll_no}:api",
    "authority_api": "authority:{auth_id}:api",
    "authority_updates": "authority:{auth_id}:updates",  # ✅ NEW
    "global": "global:api",
}


# ==================== SPAM DETECTION ====================

# Spam keywords (basic - overridden by settings)
SPAM_KEYWORDS: List[str] = [
    "spam", "test", "testing", "dummy", "fake",
    "xyz", "abc", "123", "asdf", "qwerty",
    "junk", "trash", "nonsense", "gibberish",
]

# Minimum/Maximum complaint length (overridden by settings)
MIN_COMPLAINT_LENGTH: int = 10
MAX_COMPLAINT_LENGTH: int = 2000

# Spam detection thresholds
SPAM_DETECTION_THRESHOLDS = {
    "repeated_chars": 10,  # More than 10 repeated characters
    "all_caps_threshold": 0.7,  # 70% uppercase
    "word_repetition": 5,  # Same word repeated 5+ times
}


# ==================== FILE UPLOAD ====================

# Image constraints
MAX_IMAGE_WIDTH: int = 4096
MAX_IMAGE_HEIGHT: int = 4096
IMAGE_QUALITY: int = 85  # JPEG quality

# Thumbnail sizes
THUMBNAIL_SIZES = {
    "small": (150, 150),
    "medium": (300, 300),
    "large": (800, 800),
}


# ==================== PAGINATION ====================

DEFAULT_PAGE_SIZE: int = 20
MAX_PAGE_SIZE: int = 100
MIN_PAGE_SIZE: int = 1


# ==================== TIME CONSTANTS ====================

# Auto-escalation if no response in X hours (overridden by settings)
AUTO_ESCALATE_HOURS: int = 48

# Complaint resolution SLA (hours by priority)
SLA_HOURS: Dict[str, int] = {
    "Low": 168,      # 7 days
    "Medium": 72,    # 3 days
    "High": 24,      # 1 day
    "Critical": 6,   # 6 hours
}

# Session timeout (minutes)
SESSION_TIMEOUT_MINUTES: int = 60

# Token expiration (seconds)
TOKEN_EXPIRATION_SECONDS: int = 604800  # 7 days


# ==================== REGEX PATTERNS ====================

# Email validation pattern
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')

# Roll number pattern (customize based on your college format)
# Format: 2 digits (year) + 2-3 letters (dept) + 3-4 digits (number)
# Example: 21CSE001, 22ECE0123
ROLL_NO_PATTERN = re.compile(r'^[0-9]{2}[A-Z]{2,4}[0-9]{3,4}$')

# Phone number pattern (Indian - starts with 6-9, 10 digits)
PHONE_PATTERN = re.compile(r'^[6-9]\d{9}$')

# Password strength pattern
PASSWORD_PATTERN = re.compile(
    r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&])[A-Za-z\d@$!%*?&]{8,}$'
)


# ==================== HTTP STATUS CODES ====================

HTTP_STATUS = {
    "OK": 200,
    "CREATED": 201,
    "ACCEPTED": 202,
    "NO_CONTENT": 204,
    "BAD_REQUEST": 400,
    "UNAUTHORIZED": 401,
    "FORBIDDEN": 403,
    "NOT_FOUND": 404,
    "CONFLICT": 409,
    "UNPROCESSABLE_ENTITY": 422,
    "TOO_MANY_REQUESTS": 429,
    "INTERNAL_SERVER_ERROR": 500,
    "SERVICE_UNAVAILABLE": 503,
}


# ==================== ERROR CODES ====================

ERROR_CODES = {
    # Authentication
    "AUTH_ERROR": "AUTH_001",
    "INVALID_CREDENTIALS": "AUTH_002",
    "TOKEN_EXPIRED": "AUTH_003",
    "INVALID_TOKEN": "AUTH_004",
    "ACCOUNT_INACTIVE": "AUTH_005",
    
    # Authorization
    "UNAUTHORIZED": "AUTHZ_001",
    "INSUFFICIENT_PERMISSIONS": "AUTHZ_002",
    
    # Validation
    "VALIDATION_ERROR": "VAL_001",
    "DUPLICATE_ENTRY": "VAL_002",
    
    # Resources
    "RESOURCE_NOT_FOUND": "RES_001",
    "STUDENT_NOT_FOUND": "RES_002",
    "COMPLAINT_NOT_FOUND": "RES_003",
    "AUTHORITY_NOT_FOUND": "RES_004",
    "UPDATE_NOT_FOUND": "RES_005",  # ✅ NEW
    
    # Student
    "INVALID_YEAR": "STUD_006",  # ✅ NEW
    
    # Business Logic
    "SPAM_DETECTED": "BIZ_001",
    "BLACKLISTED": "BIZ_002",
    "RATE_LIMIT_EXCEEDED": "BIZ_003",
    "INVALID_STATUS_TRANSITION": "BIZ_004",
    "DUPLICATE_VOTE": "BIZ_005",
    
    # File Upload
    "INVALID_FILE_TYPE": "FILE_001",
    "FILE_TOO_LARGE": "FILE_002",
    
    # External Services
    "LLM_SERVICE_ERROR": "EXT_001",
    "DATABASE_ERROR": "EXT_002",
    
    # ✅ NEW: Authority Updates
    "INVALID_UPDATE_TYPE": "UPD_001",
    "UPDATE_TOO_LONG": "UPD_002",
    "UPDATE_TOO_SHORT": "UPD_003",
    "UNAUTHORIZED_UPDATE": "UPD_004",
    "UPDATE_EXPIRED": "UPD_005",
}


# ==================== ERROR MESSAGES ====================

ERROR_MESSAGES = {
    "INVALID_CREDENTIALS": "Invalid email or password",
    "STUDENT_NOT_FOUND": "Student not found",
    "AUTHORITY_NOT_FOUND": "Authority not found",
    "COMPLAINT_NOT_FOUND": "Complaint not found",
    "UPDATE_NOT_FOUND": "Authority update not found",  # ✅ NEW
    "INVALID_YEAR": "Invalid year. Must be one of: 1st Year, 2nd Year, 3rd Year, 4th Year",  # ✅ NEW
    "UNAUTHORIZED": "You are not authorized to perform this action",
    "RATE_LIMIT_EXCEEDED": "Rate limit exceeded. Please try again later",
    "SPAM_DETECTED": "Your complaint has been flagged as spam",
    "BLACKLISTED": "Your account has been temporarily suspended",
    "INVALID_FILE_TYPE": "Invalid file type. Only images are allowed",
    "FILE_TOO_LARGE": "File size exceeds maximum limit",
    "INVALID_STATUS_TRANSITION": "Invalid status transition",
    "DUPLICATE_VOTE": "You have already voted on this complaint",
    "TOKEN_EXPIRED": "Your session has expired. Please login again",
    "INVALID_TOKEN": "Invalid authentication token",
    "ACCOUNT_INACTIVE": "Your account is inactive. Please contact admin",
    "INSUFFICIENT_PERMISSIONS": "You don't have permission to perform this action",
    "VALIDATION_ERROR": "Validation error in submitted data",
    "DUPLICATE_ENTRY": "This entry already exists",
    "LLM_SERVICE_ERROR": "AI service is temporarily unavailable",
    "DATABASE_ERROR": "Database operation failed",
    # ✅ NEW: Authority update errors
    "INVALID_UPDATE_TYPE": "Invalid update type",
    "UPDATE_TOO_LONG": f"Update text exceeds maximum length of {MAX_UPDATE_LENGTH} characters",
    "UPDATE_TOO_SHORT": f"Update text must be at least {MIN_UPDATE_LENGTH} characters",
    "UNAUTHORIZED_UPDATE": "You are not authorized to post/edit/delete this update",
    "UPDATE_EXPIRED": "This update has expired and cannot be modified",
}


# ==================== SUCCESS MESSAGES ====================

SUCCESS_MESSAGES = {
    "STUDENT_REGISTERED": "Student registered successfully",
    "LOGIN_SUCCESS": "Login successful",
    "COMPLAINT_SUBMITTED": "Complaint submitted successfully",
    "STATUS_UPDATED": "Complaint status updated successfully",
    "VOTE_RECORDED": "Vote recorded successfully",
    "VOTE_REMOVED": "Vote removed successfully",
    "NOTIFICATION_SENT": "Notification sent successfully",
    "PASSWORD_CHANGED": "Password changed successfully",
    "PROFILE_UPDATED": "Profile updated successfully",
    "IMAGE_UPLOADED": "Image uploaded successfully",
    "COMPLAINT_DELETED": "Complaint deleted successfully",
    "AUTHORITY_CREATED": "Authority created successfully",
    # ✅ NEW: Authority update success messages
    "UPDATE_POSTED": "Authority update posted successfully",
    "UPDATE_EDITED": "Authority update edited successfully",
    "UPDATE_DELETED": "Authority update deleted successfully",
}


# ==================== CACHE KEYS ====================

CACHE_KEY_TEMPLATES = {
    "student_profile": "student:profile:{roll_no}",
    "authority_profile": "authority:profile:{id}",
    "complaint": "complaint:{id}",
    "complaint_list": "complaints:list:{filters}",
    "departments": "departments:all",
    "categories": "categories:all",
    # ✅ NEW: Authority update cache keys
    "authority_update": "authority_update:{id}",
    "authority_updates_list": "authority_updates:{filters}",
    "student_feed": "student_feed:{roll_no}:{filters}",
    "public_feed": "public_feed:{filters}",
}

# Cache TTL (seconds)
CACHE_TTL = {
    "student_profile": 3600,  # 1 hour
    "authority_profile": 3600,
    "complaint": 300,  # 5 minutes
    "complaint_list": 60,  # 1 minute
    "departments": 86400,  # 24 hours
    "categories": 86400,
    # ✅ NEW: Authority update cache TTL
    "authority_update": 600,         # 10 minutes
    "authority_updates_list": 300,   # 5 minutes
    "student_feed": 180,              # 3 minutes
    "public_feed": 180,               # 3 minutes
}


# ==================== WEBSOCKET EVENTS ====================

WS_EVENTS = {
    "CONNECT": "connect",
    "DISCONNECT": "disconnect",
    "COMPLAINT_UPDATE": "complaint_update",
    "NEW_NOTIFICATION": "new_notification",
    "STATUS_CHANGE": "status_change",
    "NEW_COMMENT": "new_comment",
    "VOTE_UPDATE": "vote_update",
    "PING": "ping",
    "PONG": "pong",
    # ✅ NEW: Authority update WebSocket events
    "NEW_AUTHORITY_UPDATE": "new_authority_update",
    "UPDATE_EDITED": "update_edited",
    "UPDATE_DELETED": "update_deleted",
}


# ==================== DATE FORMATS ====================

DATE_FORMATS = {
    "ISO": "%Y-%m-%dT%H:%M:%S",
    "DATE_ONLY": "%Y-%m-%d",
    "TIME_ONLY": "%H:%M:%S",
    "DISPLAY": "%d %b %Y, %I:%M %p",
    "FILENAME": "%Y%m%d_%H%M%S",
}


# ==================== HELPER FUNCTIONS ====================

def get_priority_from_score(score: float) -> str:
    """
    Get priority level from score.
    
    Args:
        score: Priority score
    
    Returns:
        Priority level string
    """
    if score >= PRIORITY_SCORES["Critical"]:
        return "Critical"
    elif score >= PRIORITY_SCORES["High"]:
        return "High"
    elif score >= PRIORITY_SCORES["Medium"]:
        return "Medium"
    else:
        return "Low"


def is_valid_status_transition(current: str, new: str) -> bool:
    """
    Check if status transition is valid.
    
    Args:
        current: Current status
        new: New status
    
    Returns:
        True if transition is valid
    """
    return new in VALID_STATUS_TRANSITIONS.get(current, [])


def is_valid_year(year: str) -> bool:
    """
    Check if student year is valid.
    
    Args:
        year: Student year string
    
    Returns:
        True if year is valid
    """
    return year in VALID_YEARS


# ==================== EXPORT ====================

__all__ = [
    # Enums
    "DepartmentCode",
    "CategoryName",
    "AuthorityType",
    "ComplaintStatus",
    "PriorityLevel",
    "VisibilityLevel",
    "Gender",
    "StayType",
    "StudentYear",  # ✅ NEW
    "VoteType",
    "NotificationType",
    "LLMOperationType",
    "ImageVerificationStatus",
    "UpdatePriority",  # ✅ NEW
    "UpdateVisibility",  # ✅ NEW
    "UpdateCategory",  # ✅ NEW
    
    # Lists
    "DEPARTMENTS",
    "CATEGORIES",
    "SPAM_KEYWORDS",
    "VALID_YEARS",  # ✅ NEW
    
    # Dicts
    "AUTHORITY_LEVELS",
    "LEVEL_TO_AUTHORITY",
    "VALID_STATUS_TRANSITIONS",
    "PRIORITY_SCORES",
    "DEFAULT_CATEGORY_ROUTING",
    "ESCALATION_RULES",
    "SLA_HOURS",
    "ERROR_MESSAGES",
    "SUCCESS_MESSAGES",
    "ERROR_CODES",
    "HTTP_STATUS",
    "CACHE_KEY_TEMPLATES",
    "CACHE_TTL",
    "WS_EVENTS",
    "DATE_FORMATS",
    
    # Constants
    "VOTE_IMPACT_MULTIPLIER",
    "PRIORITY_AUTO_ESCALATE_THRESHOLD",
    "MIN_COMPLAINT_LENGTH",
    "MAX_COMPLAINT_LENGTH",
    "MAX_UPDATE_LENGTH",  # ✅ NEW
    "MIN_UPDATE_LENGTH",  # ✅ NEW
    "UPDATE_EXPIRY_DAYS",  # ✅ NEW
    "DEFAULT_PAGE_SIZE",
    "MAX_PAGE_SIZE",
    "MIN_PAGE_SIZE",
    "AUTO_ESCALATE_HOURS",
    "MAX_IMAGE_WIDTH",
    "MAX_IMAGE_HEIGHT",
    "IMAGE_QUALITY",
    "SESSION_TIMEOUT_MINUTES",
    "TOKEN_EXPIRATION_SECONDS",
    
    # Patterns
    "EMAIL_PATTERN",
    "ROLL_NO_PATTERN",
    "PHONE_PATTERN",
    "PASSWORD_PATTERN",
    
    # Helper Functions
    "get_priority_from_score",
    "is_valid_status_transition",
    "is_valid_year",  # ✅ NEW
]
