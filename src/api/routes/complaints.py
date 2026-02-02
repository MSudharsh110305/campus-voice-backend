"""
Complaint API endpoints.
CRUD operations, voting, filtering, image upload.
"""

import logging
from typing import Optional
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status, Query, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.session import get_db
from src.schemas.complaint import (
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
from src.schemas.vote import VoteCreate, VoteResponse
from src.schemas.common import SuccessResponse
from src.services.complaint_service import ComplaintService
from src.services.vote_service import VoteService
from src.utils.jwt_utils import get_current_student, get_current_authority
from src.utils.exceptions import ComplaintNotFoundError, to_http_exception
from src.utils.file_upload import file_upload_handler

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/complaints", tags=["Complaints"])


# ==================== CREATE COMPLAINT ====================

@router.post(
    "/submit",  # ✅ CHANGED from "" to "/submit"
    response_model=ComplaintSubmitResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit complaint",
    description="Submit a new complaint with LLM processing"
)
async def create_complaint(
    data: ComplaintCreate,
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Submit a new complaint.
    
    The complaint will be:
    - Categorized using AI
    - Rephrased for professionalism
    - Checked for spam
    - Routed to appropriate authority
    - Prioritized based on content
    """
    try:
        service = ComplaintService(db)
        
        result = await service.create_complaint(
            student_roll_no=roll_no,
            category_id=data.category_id,
            original_text=data.original_text,
            visibility=data.visibility or "Public"
        )
        
        return ComplaintSubmitResponse(**result)
        
    except Exception as e:
        logger.error(f"Complaint creation error: {e}")
        if isinstance(e, HTTPException):
            raise
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=str(e)
        )


# ==================== GET COMPLAINTS ====================

@router.get(
    "/public-feed",  # ✅ CHANGED from "" to "/public-feed"
    response_model=ComplaintListResponse,
    summary="Get public complaint feed",
    description="Get public complaints with visibility filtering"
)
async def get_complaints(
    roll_no: str = Depends(get_current_student),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db)
):
    """Get public complaint feed filtered by visibility rules."""
    service = ComplaintService(db)
    
    complaints = await service.get_public_feed(
        student_roll_no=roll_no,
        skip=skip,
        limit=limit
    )
    
    # Get total count (would need a separate count method)
    from src.repositories.complaint_repo import ComplaintRepository
    complaint_repo = ComplaintRepository(db)
    all_complaints = await service.get_public_feed(roll_no, skip=0, limit=10000)
    total = len(all_complaints)
    
    return ComplaintListResponse(
        complaints=[ComplaintResponse.model_validate(c) for c in complaints],
        total=total,
        page=skip // limit + 1,
        page_size=limit,
        total_pages=(total + limit - 1) // limit
    )


@router.get(
    "/{complaint_id}",
    response_model=ComplaintDetailResponse,
    summary="Get complaint details",
    description="Get detailed information about a specific complaint"
)
async def get_complaint(
    complaint_id: UUID,
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Get detailed complaint information."""
    from src.repositories.complaint_repo import ComplaintRepository
    
    complaint_repo = ComplaintRepository(db)
    complaint = await complaint_repo.get_with_relations(complaint_id)
    
    if not complaint:
        raise ComplaintNotFoundError(str(complaint_id))
    
    # Check visibility permissions
    # (implement visibility logic here)
    
    return ComplaintDetailResponse.model_validate(complaint)


# ==================== VOTING ====================

@router.post(
    "/{complaint_id}/vote",
    response_model=VoteResponse,
    summary="Vote on complaint",
    description="Upvote or downvote a complaint"
)
async def vote_on_complaint(
    complaint_id: UUID,
    data: VoteCreate,
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Vote on a complaint.
    
    - **vote_type**: Upvote or Downvote
    
    Voting affects complaint priority and visibility.
    """
    try:
        service = VoteService(db)
        
        result = await service.add_vote(
            complaint_id=complaint_id,
            student_roll_no=roll_no,
            vote_type=data.vote_type
        )
        
        return VoteResponse(
            complaint_id=complaint_id,
            upvotes=result["upvotes"],
            downvotes=result["downvotes"],
            priority_score=result["priority_score"],
            priority=result["priority"],
            user_vote=data.vote_type
        )
        
    except Exception as e:
        logger.error(f"Vote error: {e}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/{complaint_id}/vote",
    response_model=SuccessResponse,
    summary="Remove vote",
    description="Remove your vote from a complaint"
)
async def remove_vote(
    complaint_id: UUID,
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Remove vote from complaint."""
    try:
        service = VoteService(db)
        
        await service.remove_vote(
            complaint_id=complaint_id,
            student_roll_no=roll_no
        )
        
        return SuccessResponse(
            success=True,
            message="Vote removed successfully"
        )
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


# ==================== IMAGE UPLOAD ====================

@router.post(
    "/{complaint_id}/upload-image",
    response_model=ImageUploadResponse,
    summary="Upload complaint image",
    description="Upload supporting image for complaint"
)
async def upload_complaint_image(
    complaint_id: UUID,
    file: UploadFile = File(...),
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """
    Upload image for complaint.
    
    - **file**: Image file (JPEG, PNG, max 5MB)
    """
    try:
        from src.repositories.complaint_repo import ComplaintRepository
        
        complaint_repo = ComplaintRepository(db)
        complaint = await complaint_repo.get(complaint_id)
        
        if not complaint:
            raise ComplaintNotFoundError(str(complaint_id))
        
        # Check if user owns the complaint
        if complaint.student_roll_no != roll_no:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You can only upload images for your own complaints"
            )
        
        # Upload file
        file_path, metadata = await file_upload_handler.save_image(
            file,
            subfolder="complaints"
        )
        
        # Update complaint with image
        complaint.image_url = file_path
        await db.commit()
        
        logger.info(f"Image uploaded for complaint {complaint_id}")
        
        return ImageUploadResponse(
            image_url=file_path,
            verified=False,
            verification_status="Pending",
            message="Image uploaded successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Image upload error: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Image upload failed"
        )


# ==================== FILTER & SEARCH ====================

@router.get(
    "/filter/advanced",
    response_model=ComplaintListResponse,
    summary="Advanced complaint filtering",
    description="Filter complaints by multiple criteria"
)
async def filter_complaints(
    status_filter: Optional[str] = Query(None),
    priority: Optional[str] = Query(None),
    category_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    roll_no: str = Depends(get_current_student),
    db: AsyncSession = Depends(get_db)
):
    """Filter complaints with advanced criteria."""
    from src.repositories.complaint_repo import ComplaintRepository
    
    complaint_repo = ComplaintRepository(db)
    
    # Build filter conditions
    # (implement comprehensive filtering)
    
    # For now, return basic filtered list
    if status_filter:
        complaints = await complaint_repo.get_by_status(status_filter, skip, limit)
    elif priority:
        complaints = await complaint_repo.get_by_priority(priority, skip, limit)
    elif category_id:
        complaints = await complaint_repo.get_by_category(category_id, skip, limit)
    else:
        service = ComplaintService(db)
        complaints = await service.get_public_feed(roll_no, skip, limit)
    
    return ComplaintListResponse(
        complaints=[ComplaintResponse.model_validate(c) for c in complaints],
        total=len(complaints),
        page=skip // limit + 1,
        page_size=limit,
        total_pages=1
    )


__all__ = ["router"]
