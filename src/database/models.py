"""
SQLAlchemy ORM models for CampusVoice.
All database tables with relationships, constraints, and indexes.
"""

from datetime import datetime
from uuid import uuid4
from sqlalchemy import (
    Column, String, Integer, Float, Boolean, DateTime, Text,
    ForeignKey, BigInteger, CheckConstraint, Index, UniqueConstraint
)
from sqlalchemy.dialects.postgresql import UUID, JSONB, ARRAY
from sqlalchemy.orm import declarative_base, relationship
from sqlalchemy.sql import func

Base = declarative_base()


# ==================== CORE TABLES ====================

class Department(Base):
    """Department model - 13 engineering departments"""
    __tablename__ = "departments"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Department Info
    code = Column(String(10), unique=True, nullable=False, index=True)
    name = Column(String(255), nullable=False)
    
    # HOD Info (optional)
    hod_name = Column(String(255), nullable=True)
    hod_email = Column(String(255), nullable=True)
    hod_phone = Column(String(20), nullable=True)
    
    # Stats
    total_students = Column(Integer, default=0, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    students = relationship("Student", back_populates="department")
    authorities = relationship("Authority", back_populates="department")
    complaints = relationship("Complaint", back_populates="complaint_department")
    
    def __repr__(self):
        return f"<Department(code={self.code}, name={self.name})>"


class ComplaintCategory(Base):
    """Complaint category model - 4 fixed categories"""
    __tablename__ = "complaint_categories"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Category Info
    name = Column(String(100), unique=True, nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Keywords for LLM categorization
    keywords = Column(ARRAY(String), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    complaints = relationship("Complaint", back_populates="category")
    routing_rules = relationship("AuthorityRoutingRule", back_populates="category")
    
    def __repr__(self):
        return f"<ComplaintCategory(name={self.name})>"


class Student(Base):
    """Student model - registered students who submit complaints"""
    __tablename__ = "students"
    
    # Primary Key
    roll_no = Column(String(20), primary_key=True, index=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    
    # Profile
    gender = Column(String(10), nullable=False)
    stay_type = Column(String(20), nullable=False)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    email_verified = Column(Boolean, default=False, nullable=False)
    verification_token = Column(String(255), nullable=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="students")
    complaints = relationship("Complaint", back_populates="student", cascade="all, delete-orphan")
    votes = relationship("Vote", back_populates="student", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("gender IN ('Male', 'Female', 'Other')", name="check_gender"),
        CheckConstraint("stay_type IN ('Hostel', 'Day Scholar')", name="check_stay_type"),
    )
    
    def __repr__(self):
        return f"<Student(roll_no={self.roll_no}, name={self.name})>"


class Authority(Base):
    """Authority model - wardens, HODs, admin officers, etc."""
    __tablename__ = "authorities"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Basic Info
    name = Column(String(255), nullable=False)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=True)
    
    # Authority Details
    authority_type = Column(String(100), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="SET NULL"), nullable=True, index=True)
    designation = Column(String(255), nullable=True)
    authority_level = Column(Integer, nullable=False, index=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    department = relationship("Department", back_populates="authorities")
    assigned_complaints = relationship(
        "Complaint",
        foreign_keys="Complaint.assigned_authority_id",
        back_populates="assigned_authority"
    )
    status_updates = relationship("StatusUpdate", back_populates="updated_by_authority")
    spam_flags = relationship("Complaint", foreign_keys="Complaint.spam_flagged_by", back_populates="spam_flagged_by_authority")
    
    def __repr__(self):
        return f"<Authority(name={self.name}, type={self.authority_type})>"


class Complaint(Base):
    """Complaint model - main table for student complaints"""
    __tablename__ = "complaints"
    
    # Primary Key - UUID for security
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid4)
    
    # Foreign Keys
    student_roll_no = Column(String(20), ForeignKey("students.roll_no", ondelete="CASCADE"), nullable=False, index=True)
    category_id = Column(Integer, ForeignKey("complaint_categories.id", ondelete="RESTRICT"), nullable=False, index=True)
    
    # Content
    original_text = Column(Text, nullable=False)
    rephrased_text = Column(Text, nullable=True)
    
    # Visibility
    visibility = Column(String(50), default="Private", nullable=False, index=True)
    
    # Voting
    upvotes = Column(Integer, default=0, nullable=False)
    downvotes = Column(Integer, default=0, nullable=False)
    
    # Priority
    priority_score = Column(Float, default=0.0, nullable=False, index=True)
    priority = Column(String(20), default="Medium", nullable=False, index=True)
    
    # Assignment
    assigned_authority_id = Column(
        BigInteger,
        ForeignKey("authorities.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    assigned_at = Column(DateTime(timezone=True), nullable=True)
    original_assigned_authority_id = Column(BigInteger, nullable=True)
    
    # Status
    status = Column(String(50), default="Raised", nullable=False, index=True)
    
    # Spam Detection
    is_marked_as_spam = Column(Boolean, default=False, nullable=False, index=True)
    spam_reason = Column(Text, nullable=True)
    spam_flagged_by = Column(BigInteger, ForeignKey("authorities.id", ondelete="SET NULL"), nullable=True)
    spam_flagged_at = Column(DateTime(timezone=True), nullable=True)
    
    # Image
    image_url = Column(Text, nullable=True)
    image_verified = Column(Boolean, default=False, nullable=False)
    image_verification_status = Column(String(50), nullable=True)
    
    # Department tracking
    complaint_department_id = Column(
        Integer,
        ForeignKey("departments.id", ondelete="SET NULL"),
        nullable=True,
        index=True
    )
    is_cross_department = Column(Boolean, default=False, nullable=False)
    
    # Timestamps
    submitted_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    resolved_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    student = relationship("Student", back_populates="complaints")
    category = relationship("ComplaintCategory", back_populates="complaints")
    assigned_authority = relationship(
        "Authority",
        foreign_keys=[assigned_authority_id],
        back_populates="assigned_complaints"
    )
    spam_flagged_by_authority = relationship(
        "Authority",
        foreign_keys=[spam_flagged_by],
        back_populates="spam_flags"
    )
    complaint_department = relationship("Department", back_populates="complaints")
    votes = relationship("Vote", back_populates="complaint", cascade="all, delete-orphan")
    status_updates = relationship("StatusUpdate", back_populates="complaint", cascade="all, delete-orphan")
    image_verification_logs = relationship("ImageVerificationLog", back_populates="complaint", cascade="all, delete-orphan")
    llm_logs = relationship("LLMProcessingLog", back_populates="complaint", cascade="all, delete-orphan")
    notifications = relationship("Notification", back_populates="complaint", cascade="all, delete-orphan")
    comments = relationship("Comment", back_populates="complaint", cascade="all, delete-orphan")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("visibility IN ('Private', 'Department', 'Public')", name="check_visibility"),
        CheckConstraint("status IN ('Raised', 'In Progress', 'Resolved', 'Closed', 'Spam')", name="check_status"),
        CheckConstraint("priority IN ('Low', 'Medium', 'High', 'Critical')", name="check_priority"),
        CheckConstraint("upvotes >= 0", name="check_upvotes"),
        CheckConstraint("downvotes >= 0", name="check_downvotes"),
        Index("idx_complaint_status_priority", "status", "priority_score"),
        Index("idx_complaint_student_status", "student_roll_no", "status"),
    )
    
    def __repr__(self):
        return f"<Complaint(id={self.id}, status={self.status}, priority={self.priority})>"


class Vote(Base):
    """Vote model - upvotes/downvotes on complaints"""
    __tablename__ = "votes"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Keys - UUID for complaint_id
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    student_roll_no = Column(String(20), ForeignKey("students.roll_no", ondelete="CASCADE"), nullable=False, index=True)
    
    # Vote Type
    vote_type = Column(String(10), nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    complaint = relationship("Complaint", back_populates="votes")
    student = relationship("Student", back_populates="votes")
    
    # Constraints
    __table_args__ = (
        UniqueConstraint("complaint_id", "student_roll_no", name="unique_vote_per_student"),
        CheckConstraint("vote_type IN ('Upvote', 'Downvote')", name="check_vote_type"),
    )
    
    def __repr__(self):
        return f"<Vote(complaint_id={self.complaint_id}, type={self.vote_type})>"


class StatusUpdate(Base):
    """Status update model - audit trail for complaint status changes"""
    __tablename__ = "status_updates"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    updated_by = Column(BigInteger, ForeignKey("authorities.id", ondelete="SET NULL"), nullable=True)
    
    # Status Change
    old_status = Column(String(50), nullable=False)
    new_status = Column(String(50), nullable=False)
    reason = Column(Text, nullable=True)
    
    # Timestamp
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Relationships
    complaint = relationship("Complaint", back_populates="status_updates")
    updated_by_authority = relationship("Authority", back_populates="status_updates")
    
    def __repr__(self):
        return f"<StatusUpdate({self.old_status} → {self.new_status})>"


# ==================== SUPPORT TABLES ====================

class AuthorityRoutingRule(Base):
    """Authority routing rules - complaint routing configuration"""
    __tablename__ = "authority_routing_rules"
    
    # Primary Key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Foreign Keys
    category_id = Column(Integer, ForeignKey("complaint_categories.id", ondelete="CASCADE"), nullable=False, index=True)
    department_id = Column(Integer, ForeignKey("departments.id", ondelete="CASCADE"), nullable=True, index=True)
    authority_id = Column(BigInteger, ForeignKey("authorities.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Priority
    priority_level = Column(Integer, default=1, nullable=False)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    
    # Timestamp
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    category = relationship("ComplaintCategory", back_populates="routing_rules")
    
    def __repr__(self):
        return f"<AuthorityRoutingRule(category_id={self.category_id})>"


class ImageVerificationLog(Base):
    """Image verification log - LLM image relevance check"""
    __tablename__ = "image_verification_logs"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Key - UUID
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Image Info
    image_url = Column(Text, nullable=False)
    
    # LLM Response
    llm_response = Column(JSONB, nullable=True)
    is_relevant = Column(Boolean, nullable=False)
    confidence_score = Column(Float, nullable=True)
    rejection_reason = Column(Text, nullable=True)
    
    # Timestamp
    verified_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    
    # Relationships
    complaint = relationship("Complaint", back_populates="image_verification_logs")
    
    def __repr__(self):
        return f"<ImageVerificationLog(relevant={self.is_relevant})>"


class SpamBlacklist(Base):
    """Spam blacklist - tracks students flagged for spam"""
    __tablename__ = "spam_blacklist"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Key
    student_roll_no = Column(String(20), ForeignKey("students.roll_no", ondelete="CASCADE"), nullable=False, index=True)
    
    # Spam Info
    reason = Column(Text, nullable=False)
    spam_count = Column(Integer, default=1, nullable=False)
    is_permanent = Column(Boolean, default=False, nullable=False)
    
    # Who flagged
    blacklisted_by = Column(BigInteger, ForeignKey("authorities.id", ondelete="SET NULL"), nullable=True)
    
    # Timestamps
    blacklisted_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    expires_at = Column(DateTime(timezone=True), nullable=True)
    
    def __repr__(self):
        return f"<SpamBlacklist(student={self.student_roll_no})>"


class LLMProcessingLog(Base):
    """LLM processing log - tracks all LLM API calls"""
    __tablename__ = "llm_processing_logs"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Key - UUID
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Operation Info
    operation_type = Column(String(100), nullable=False, index=True)
    prompt_used = Column(Text, nullable=True)
    llm_response = Column(Text, nullable=True)
    
    # Metrics
    tokens_used = Column(Integer, nullable=True)
    processing_time_ms = Column(Integer, nullable=True)
    cost = Column(Float, nullable=True)
    
    # Status
    status = Column(String(50), nullable=False)
    error_message = Column(Text, nullable=True)
    
    # Timestamp
    processed_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    # Relationships
    complaint = relationship("Complaint", back_populates="llm_logs")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("status IN ('Success', 'Failed', 'Timeout')", name="check_status_log"),
        Index("idx_llm_operation_status", "operation_type", "status"),
    )
    
    def __repr__(self):
        return f"<LLMProcessingLog(operation={self.operation_type})>"


class Notification(Base):
    """Notification model - real-time alerts"""
    __tablename__ = "notifications"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Recipient
    recipient_type = Column(String(50), nullable=False, index=True)
    recipient_id = Column(String(255), nullable=False, index=True)
    
    # Content
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=True, index=True)
    notification_type = Column(String(100), nullable=False, index=True)
    message = Column(Text, nullable=False)
    
    # Read Status
    is_read = Column(Boolean, default=False, nullable=False, index=True)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    read_at = Column(DateTime(timezone=True), nullable=True)
    
    # Relationships
    complaint = relationship("Complaint", back_populates="notifications")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("recipient_type IN ('Student', 'Authority')", name="check_recipient_type"),
        Index("idx_notification_recipient_unread", "recipient_id", "is_read"),
    )
    
    def __repr__(self):
        return f"<Notification(type={self.notification_type})>"


class Comment(Base):
    """Comment model - comments on complaints"""
    __tablename__ = "comments"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Foreign Key - UUID
    complaint_id = Column(UUID(as_uuid=True), ForeignKey("complaints.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Author
    author_id = Column(String(255), nullable=False, index=True)
    author_type = Column(String(50), nullable=False)
    
    # Content
    comment_text = Column(Text, nullable=False)
    is_anonymous = Column(Boolean, default=True, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime(timezone=True), nullable=False, default=func.now())
    updated_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), onupdate=func.now())
    
    # Relationships
    complaint = relationship("Complaint", back_populates="comments")
    
    # Constraints
    __table_args__ = (
        CheckConstraint("author_type IN ('Student', 'Authority')", name="check_author_type"),
    )
    
    def __repr__(self):
        return f"<Comment(author={self.author_id})>"


class AdminAuditLog(Base):
    """Admin audit log - tracks all admin actions"""
    __tablename__ = "admin_audit_log"
    
    # Primary Key
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    
    # Admin
    admin_id = Column(BigInteger, ForeignKey("authorities.id", ondelete="SET NULL"), nullable=True, index=True)
    
    # Action
    action = Column(String(255), nullable=False, index=True)
    target_type = Column(String(100), nullable=True)
    target_id = Column(String(255), nullable=True)
    
    # Changes
    changes = Column(JSONB, nullable=True)
    
    # Timestamp
    action_at = Column(DateTime(timezone=True), nullable=False, default=func.now(), index=True)
    
    def __repr__(self):
        return f"<AdminAuditLog(action={self.action})>"


# ==================== EXPORT ====================

__all__ = [
    "Base",
    "Department",
    "ComplaintCategory",
    "Student",
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
