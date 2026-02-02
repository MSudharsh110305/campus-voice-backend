"""
Admin API endpoints.
System administration, user management, analytics.
"""

import logging
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.schemas.authority import AuthorityCreate, AuthorityListResponse
from src.schemas.common import SuccessResponse
from src.repositories.authority_repo import AuthorityRepository
from src.repositories.student_repo import StudentRepository
from src.repositories.complaint_repo import ComplaintRepository
from src.services.auth_service import auth_service
from src.utils.jwt_utils import get_current_authority

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/admin", tags=["Admin"])


# ==================== AUTHORITY MANAGEMENT ====================

@router.post(
    "/authorities",
    response_model=SuccessResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create authority",
    description="Create new authority account (admin only)"
)
async def create_authority(
    data: AuthorityCreate,
    current_authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """
    Create new authority account.
    
    Requires admin privileges.
    """
    # Check if current user is admin
    authority_repo = AuthorityRepository(db)
    current_authority = await authority_repo.get(current_authority_id)
    
    if not current_authority or current_authority.authority_type != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    # Check if email already exists
    existing = await authority_repo.get_by_email(data.email)
    if existing:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Email already registered"
        )
    
    # Hash password
    password_hash = auth_service.hash_password(data.password)
    
    # Create authority
    await authority_repo.create(
        name=data.name,
        email=data.email,
        password_hash=password_hash,
        phone=data.phone,
        authority_type=data.authority_type,
        department_id=data.department_id,
        designation=data.designation,
        authority_level=data.authority_level
    )
    
    logger.info(f"Authority created: {data.email}")
    
    return SuccessResponse(
        success=True,
        message="Authority created successfully"
    )


@router.get(
    "/authorities",
    response_model=AuthorityListResponse,
    summary="List authorities",
    description="Get list of all authorities (admin only)"
)
async def list_authorities(
    current_authority_id: int = Depends(get_current_authority),
    skip: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """List all authorities."""
    authority_repo = AuthorityRepository(db)
    
    # Check admin access
    current_authority = await authority_repo.get(current_authority_id)
    if not current_authority or current_authority.authority_type != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    authorities = await authority_repo.get_active_authorities(skip, limit)
    total = await authority_repo.count(is_active=True)
    
    from src.schemas.authority import AuthorityProfile
    
    return AuthorityListResponse(
        authorities=[AuthorityProfile.model_validate(a) for a in authorities],
        total=total
    )


# ==================== SYSTEM STATISTICS ====================

@router.get(
    "/stats/overview",
    summary="System overview statistics",
    description="Get overall system statistics (admin only)"
)
async def get_system_stats(
    current_authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get system-wide statistics."""
    authority_repo = AuthorityRepository(db)
    
    # Check admin access
    current_authority = await authority_repo.get(current_authority_id)
    if not current_authority or current_authority.authority_type != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    student_repo = StudentRepository(db)
    complaint_repo = ComplaintRepository(db)
    
    # Get counts
    total_students = await student_repo.count()
    total_authorities = await authority_repo.count()
    total_complaints = await complaint_repo.count()
    
    # Get complaint stats
    status_counts = await complaint_repo.count_by_status()
    priority_counts = await complaint_repo.count_by_priority()
    category_counts = await complaint_repo.count_by_category()
    
    return {
        "total_students": total_students,
        "total_authorities": total_authorities,
        "total_complaints": total_complaints,
        "complaints_by_status": status_counts,
        "complaints_by_priority": priority_counts,
        "complaints_by_category": category_counts
    }


# ==================== USER MANAGEMENT ====================

@router.post(
    "/students/{roll_no}/deactivate",
    response_model=SuccessResponse,
    summary="Deactivate student",
    description="Deactivate student account (admin only)"
)
async def deactivate_student(
    roll_no: str,
    current_authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Deactivate student account."""
    authority_repo = AuthorityRepository(db)
    
    # Check admin access
    current_authority = await authority_repo.get(current_authority_id)
    if not current_authority or current_authority.authority_type != "Admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    
    student_repo = StudentRepository(db)
    student = await student_repo.get(roll_no)
    
    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Student not found"
        )
    
    await student_repo.update(roll_no, is_active=False)
    
    logger.info(f"Student deactivated: {roll_no}")
    
    return SuccessResponse(
        success=True,
        message="Student account deactivated"
    )


__all__ = ["router"]
