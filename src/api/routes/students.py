"""
Student API endpoints.
Registration, login, profile management, statistics.
"""

import logging
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.schemas.student import (
    StudentRegister,
    StudentLogin,
    StudentProfile,
    StudentProfileUpdate,
    StudentResponse,
    StudentStats,
    PasswordChange,
)
from src.schemas.common import SuccessResponse, ErrorResponse
from src.repositories.student_repo import StudentRepository
from src.services.auth_service import auth_service
from src.utils.jwt_utils import get_current_student
from src.utils.exceptions import (
    InvalidCredentialsError,
    DuplicateEntryError,
    StudentNotFoundError,
    to_http_exception,
)
from src.utils.rate_limiter import rate_limiter

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/students", tags=["Students"])


# ==================== REGISTRATION ====================

@router.post(
    "/register",
    response_model=StudentResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new student",
    description="Register a new student account with email verification"
)
async def register_student(
    data: StudentRegister,
    db: AsyncSession = Depends(get_db)
):
    """
    Register a new student account.
    
    - **roll_no**: Unique roll number
    - **name**: Full name
    - **email**: College email address
    - **password**: Strong password (min 8 chars, uppercase, lowercase, digit)
    - **gender**: Male, Female, or Other
    - **stay_type**: Hostel or Day Scholar
    - **department_id**: Department ID
    """
    try:
        student_repo = StudentRepository(db)
        
        # Check if email already exists
        existing_email = await student_repo.get_by_email(data.email)
        if existing_email:
            raise HTTPException(  # ✅ Changed from DuplicateEntryError
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Email already registered"
            )
        
        # Check if roll number already exists
        existing_roll = await student_repo.get_by_roll_no(data.roll_no)
        if existing_roll:
            raise HTTPException(  # ✅ Changed from DuplicateEntryError
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Roll number already registered"
            )
        
        # Hash password
        password_hash = auth_service.hash_password(data.password)
        
        # Create student
        student = await student_repo.create(
            roll_no=data.roll_no,
            name=data.name,
            email=data.email,
            password_hash=password_hash,
            gender=data.gender,
            stay_type=data.stay_type,
            department_id=data.department_id,
        )
        
        # Generate JWT token
        token = auth_service.create_access_token(
            subject=student.roll_no,
            role="Student"
        )
        
        logger.info(f"Student registered: {student.roll_no}")
        
        return StudentResponse(
            roll_no=student.roll_no,
            name=student.name,
            email=student.email,
            token=token,
            token_type="Bearer",
            expires_in=auth_service.get_token_expiration_seconds()
        )
        
    except HTTPException:  # ✅ Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Registration error: {e}", exc_info=True)  # ✅ Added exc_info
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Registration failed"
        )


# ==================== LOGIN ====================

@router.post(
    "/login",
    response_model=StudentResponse,
    summary="Student login",
    description="Login with email/roll number and password"
)
async def login_student(
    data: StudentLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login to student account.
    
    - **email_or_roll_no**: Email address or roll number
    - **password**: Account password
    """
    try:
        student_repo = StudentRepository(db)
        
        # Check if input is email or roll number
        if "@" in data.email_or_roll_no:
            student = await student_repo.get_by_email(data.email_or_roll_no)
        else:
            student = await student_repo.get_by_roll_no(data.email_or_roll_no)
        
        # ✅ Check if student exists
        if not student:
            raise HTTPException(  # ✅ Changed from InvalidCredentialsError
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Verify password
        if not auth_service.verify_password(data.password, student.password_hash):
            raise HTTPException(  # ✅ Changed from InvalidCredentialsError
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password"
            )
        
        # Check if account is active
        if not student.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Generate JWT token
        token = auth_service.create_access_token(
            subject=student.roll_no,
            role="Student"
        )
        
        logger.info(f"Student logged in: {student.roll_no}")
        
        return StudentResponse(
            roll_no=student.roll_no,
            name=student.name,
            email=student.email,
            token=token,
            token_type="Bearer",
            expires_in=auth_service.get_token_expiration_seconds()
        )
        
    except HTTPException:  # ✅ Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.error(f"Login error: {e}", exc_info=True)  # ✅ Added exc_info
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


# ==================== PROFILE ====================

@router.get(
    "/profile",
    response_model=StudentProfile,
    summary="Get student profile",
    description="Get current student's profile information"
)
async def get_profile(
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get current student's profile."""
    student_repo = StudentRepository(db)
    
    student = await student_repo.get_with_department(roll_no)
    if not student:
        raise StudentNotFoundError(roll_no)
    
    return StudentProfile(
        roll_no=student.roll_no,
        name=student.name,
        email=student.email,
        gender=student.gender,
        stay_type=student.stay_type,
        department_id=student.department_id,
        department_name=student.department.name if student.department else None,
        department_code=student.department.code if student.department else None,
        is_active=student.is_active,
        email_verified=student.email_verified,
        created_at=student.created_at
    )


@router.put(
    "/profile",
    response_model=StudentProfile,
    summary="Update student profile",
    description="Update student profile information"
)
async def update_profile(
    data: StudentProfileUpdate,
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Update current student's profile."""
    student_repo = StudentRepository(db)
    
    # Build update dict (only include provided fields)
    update_data = data.model_dump(exclude_unset=True)
    
    if not update_data:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No fields to update"
        )
    
    # Update student
    student = await student_repo.update(roll_no, **update_data)
    if not student:
        raise StudentNotFoundError(roll_no)
    
    logger.info(f"Profile updated: {roll_no}")
    
    # Return updated profile
    student = await student_repo.get_with_department(roll_no)
    return StudentProfile.model_validate(student)


# ==================== PASSWORD ====================

@router.post(
    "/change-password",
    response_model=SuccessResponse,
    summary="Change password",
    description="Change student account password"
)
async def change_password(
    data: PasswordChange,
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Change student password."""
    student_repo = StudentRepository(db)
    
    student = await student_repo.get(roll_no)
    if not student:
        raise StudentNotFoundError(roll_no)
    
    # Verify old password
    if not auth_service.verify_password(data.old_password, student.password_hash):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect old password"
        )
    
    # Hash new password
    new_password_hash = auth_service.hash_password(data.new_password)
    
    # Update password
    await student_repo.update_password(roll_no, new_password_hash)
    
    logger.info(f"Password changed: {roll_no}")
    
    return SuccessResponse(
        success=True,
        message="Password changed successfully"
    )


# ==================== STATISTICS ====================

@router.get(
    "/stats",
    response_model=StudentStats,
    summary="Get student statistics",
    description="Get complaint statistics for current student"
)
async def get_student_stats(
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for current student."""
    from src.repositories.complaint_repo import ComplaintRepository
    from src.repositories.vote_repo import VoteRepository
    
    complaint_repo = ComplaintRepository(db)
    vote_repo = VoteRepository(db)
    
    # Get complaints by status
    all_complaints = await complaint_repo.get_by_student(roll_no)
    
    stats = {
        "total_complaints": len(all_complaints),
        "raised": len([c for c in all_complaints if c.status == "Raised"]),
        "in_progress": len([c for c in all_complaints if c.status == "In Progress"]),
        "resolved": len([c for c in all_complaints if c.status == "Resolved"]),
        "closed": len([c for c in all_complaints if c.status == "Closed"]),
        "spam": len([c for c in all_complaints if c.is_marked_as_spam]),
    }
    
    # Get votes cast
    votes = await vote_repo.get_votes_by_student(roll_no)
    stats["total_votes_cast"] = len(votes)
    
    return StudentStats(**stats)


# ==================== MY COMPLAINTS ====================

@router.get(
    "/my-complaints",
    summary="Get my complaints",
    description="Get all complaints submitted by current student"
)
async def get_my_complaints(
    roll_no: str = Depends(get_current_student),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None, description="Filter by status"),
    db: AsyncSession = Depends(get_db)
):
    """Get complaints submitted by current student."""
    from src.repositories.complaint_repo import ComplaintRepository
    from src.schemas.complaint import ComplaintListResponse, ComplaintResponse
    
    complaint_repo = ComplaintRepository(db)
    
    complaints = await complaint_repo.get_by_student(
        roll_no,
        skip=skip,
        limit=limit,
        status=status_filter
    )
    
    # Get total count
    all_complaints = await complaint_repo.get_by_student(roll_no, status=status_filter)
    total = len(all_complaints)
    
    return ComplaintListResponse(
        complaints=[ComplaintResponse.model_validate(c) for c in complaints],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


__all__ = ["router"]
