"""
Authority API endpoints.
Login, dashboard, complaint management, status updates.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.schemas.authority import (
    AuthorityLogin,
    AuthorityProfile,
    AuthorityResponse,
    AuthorityStats,
    AuthorityDashboard,
)
from src.schemas.complaint import ComplaintUpdate, ComplaintListResponse, ComplaintResponse
from src.schemas.common import SuccessResponse
from src.repositories.authority_repo import AuthorityRepository
from src.repositories.complaint_repo import ComplaintRepository
from src.services.auth_service import auth_service
from src.services.complaint_service import ComplaintService
from src.utils.jwt_utils import get_current_authority
from src.utils.exceptions import InvalidCredentialsError, AuthorityNotFoundError, to_http_exception

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/authorities", tags=["Authorities"])


# ==================== LOGIN ====================

@router.post(
    "/login",
    response_model=AuthorityResponse,
    summary="Authority login",
    description="Login for authority/admin users"
)
async def login_authority(
    data: AuthorityLogin,
    db: AsyncSession = Depends(get_db)
):
    """
    Login to authority account.
    
    - **email**: Authority email address
    - **password**: Account password
    """
    try:
        authority_repo = AuthorityRepository(db)
        
        authority = await authority_repo.get_by_email(data.email)
        
        if not authority:
            raise InvalidCredentialsError()
        
        # Verify password
        if not auth_service.verify_password(data.password, authority.password_hash):
            raise InvalidCredentialsError()
        
        # Check if account is active
        if not authority.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Account is inactive"
            )
        
        # Generate JWT token
        token = auth_service.create_access_token(
            subject=str(authority.id),
            role="Authority"
        )
        
        logger.info(f"Authority logged in: {authority.email}")
        
        return AuthorityResponse(
            id=authority.id,
            name=authority.name,
            email=authority.email,
            authority_type=authority.authority_type,
            department_id=authority.department_id,
            token=token,
            token_type="Bearer",
            expires_in=auth_service.get_token_expiration_seconds()
        )
        
    except InvalidCredentialsError as e:
        raise to_http_exception(e)
    except Exception as e:
        logger.error(f"Authority login error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Login failed"
        )


# ==================== PROFILE & DASHBOARD ====================

@router.get(
    "/profile",
    response_model=AuthorityProfile,
    summary="Get authority profile",
    description="Get current authority's profile"
)
async def get_authority_profile(
    authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get current authority's profile."""
    authority_repo = AuthorityRepository(db)
    
    authority = await authority_repo.get_with_department(authority_id)
    if not authority:
        raise AuthorityNotFoundError(authority_id)
    
    return AuthorityProfile.model_validate(authority)


@router.get(
    "/dashboard",
    response_model=AuthorityDashboard,
    summary="Get authority dashboard",
    description="Get dashboard data with stats and recent complaints"
)
async def get_authority_dashboard(
    authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get authority dashboard with statistics and recent complaints."""
    authority_repo = AuthorityRepository(db)
    complaint_repo = ComplaintRepository(db)
    
    # Get profile
    authority = await authority_repo.get_with_department(authority_id)
    if not authority:
        raise AuthorityNotFoundError(authority_id)
    
    # Get assigned complaints
    assigned_complaints = await complaint_repo.get_assigned_to_authority(authority_id)
    
    # Calculate stats
    stats = {
        "total_assigned": len(assigned_complaints),
        "pending": len([c for c in assigned_complaints if c.status == "Raised"]),
        "in_progress": len([c for c in assigned_complaints if c.status == "In Progress"]),
        "resolved": len([c for c in assigned_complaints if c.status == "Resolved"]),
        "closed": len([c for c in assigned_complaints if c.status == "Closed"]),
        "spam_flagged": len([c for c in assigned_complaints if c.is_marked_as_spam]),
        "avg_resolution_time_hours": None,  # Calculate from resolved complaints
        "performance_rating": None,
    }
    
    # Get recent complaints
    recent = await complaint_repo.get_assigned_to_authority(authority_id, skip=0, limit=10)
    
    # Get urgent complaints
    urgent = [c for c in assigned_complaints if c.priority in ["High", "Critical"]][:10]
    
    return AuthorityDashboard(
        profile=AuthorityProfile.model_validate(authority),
        stats=AuthorityStats(**stats),
        recent_complaints=[ComplaintResponse.model_validate(c) for c in recent],
        urgent_complaints=[ComplaintResponse.model_validate(c) for c in urgent],
        unread_notifications=0  # Implement notification count
    )


# ==================== COMPLAINT MANAGEMENT ====================

@router.get(
    "/complaints",
    response_model=ComplaintListResponse,
    summary="Get assigned complaints",
    description="Get all complaints assigned to current authority"
)
async def get_assigned_complaints(
    authority_id: int = Depends(get_current_authority),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    status_filter: Optional[str] = Query(None),
    db: AsyncSession = Depends(get_db)
):
    """Get complaints assigned to current authority."""
    complaint_repo = ComplaintRepository(db)
    
    complaints = await complaint_repo.get_assigned_to_authority(
        authority_id,
        skip=skip,
        limit=limit,
        status=status_filter
    )
    
    # Get total
    all_complaints = await complaint_repo.get_assigned_to_authority(
        authority_id,
        status=status_filter
    )
    total = len(all_complaints)
    
    return ComplaintListResponse(
        complaints=[ComplaintResponse.model_validate(c) for c in complaints],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.put(
    "/complaints/{complaint_id}/status",
    response_model=SuccessResponse,
    summary="Update complaint status",
    description="Update status of assigned complaint"
)
async def update_complaint_status(
    complaint_id: UUID,
    data: ComplaintUpdate,
    authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """
    Update complaint status.
    
    - **status**: New status (Raised, In Progress, Resolved, Closed)
    - **reason**: Optional reason for status change
    """
    try:
        service = ComplaintService(db)
        
        await service.update_complaint_status(
            complaint_id=complaint_id,
            new_status=data.status,
            authority_id=authority_id,
            reason=data.reason
        )
        
        return SuccessResponse(
            success=True,
            message=f"Complaint status updated to '{data.status}'"
        )
        
    except PermissionError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not authorized to update this complaint"
        )
    except Exception as e:
        logger.error(f"Status update error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== STATISTICS ====================

@router.get(
    "/stats",
    response_model=AuthorityStats,
    summary="Get authority statistics",
    description="Get performance statistics for current authority"
)
async def get_authority_stats(
    authority_id: int = Depends(get_current_authority),
    db: AsyncSession = Depends(get_db)
):
    """Get statistics for current authority."""
    complaint_repo = ComplaintRepository(db)
    
    assigned_complaints = await complaint_repo.get_assigned_to_authority(authority_id)
    
    stats = {
        "total_assigned": len(assigned_complaints),
        "pending": len([c for c in assigned_complaints if c.status == "Raised"]),
        "in_progress": len([c for c in assigned_complaints if c.status == "In Progress"]),
        "resolved": len([c for c in assigned_complaints if c.status == "Resolved"]),
        "closed": len([c for c in assigned_complaints if c.status == "Closed"]),
        "spam_flagged": len([c for c in assigned_complaints if c.is_marked_as_spam]),
        "avg_resolution_time_hours": None,
        "performance_rating": None,
    }
    
    return AuthorityStats(**stats)


__all__ = ["router"]
