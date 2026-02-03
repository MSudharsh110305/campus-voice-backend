"""
Complaint repository with specialized queries.

✅ FIXED: Added create() method with image binary support
✅ FIXED: Added image-specific query methods
✅ FIXED: Updated get_with_relations() to include image verification logs
"""

from typing import Optional, List, Dict, Any
from uuid import UUID
from datetime import datetime, timezone, timedelta
from sqlalchemy import select, func, and_, or_, desc
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from src.database.models import Complaint, Student, Authority, ComplaintCategory
from src.repositories.base import BaseRepository


class ComplaintRepository(BaseRepository[Complaint]):
    """Repository for Complaint operations"""
    
    def __init__(self, session: AsyncSession):
        super().__init__(session, Complaint)
    
    # ==================== CREATE OPERATIONS ====================
    
    async def create(
        self,
        student_roll_no: str,
        category_id: int,
        original_text: str,
        rephrased_text: str,
        visibility: str,
        priority: str,
        priority_score: float,
        status: str,
        is_marked_as_spam: bool = False,
        spam_reason: Optional[str] = None,
        complaint_department_id: Optional[int] = None,
        # ✅ NEW: Image binary parameters
        image_data: Optional[bytes] = None,
        image_filename: Optional[str] = None,
        image_mimetype: Optional[str] = None,
        image_size: Optional[int] = None,
        thumbnail_data: Optional[bytes] = None,
        thumbnail_size: Optional[int] = None,
        image_verified: bool = False,
        image_verification_status: Optional[str] = None
    ) -> Complaint:
        """
        Create new complaint with optional image.
        
        Args:
            student_roll_no: Student roll number
            category_id: Category ID
            original_text: Original complaint text
            rephrased_text: Rephrased text from LLM
            visibility: Visibility level (Private/Department/Public)
            priority: Priority level (Low/Medium/High/Critical)
            priority_score: Numeric priority score
            status: Initial status (Raised/Spam)
            is_marked_as_spam: Whether complaint is spam
            spam_reason: Reason if marked as spam
            complaint_department_id: Department ID
            image_data: Image binary data
            image_filename: Original filename
            image_mimetype: MIME type (image/jpeg, image/png)
            image_size: Size in bytes
            thumbnail_data: Thumbnail binary data
            thumbnail_size: Thumbnail size in bytes
            image_verified: Whether image is verified
            image_verification_status: Verification status (Pending/Verified/Rejected)
        
        Returns:
            Created complaint
        """
        # ✅ FIXED: Use timezone-aware datetime
        current_time = datetime.now(timezone.utc)
        
        complaint = Complaint(
            student_roll_no=student_roll_no,
            category_id=category_id,
            original_text=original_text,
            rephrased_text=rephrased_text,
            visibility=visibility,
            priority=priority,
            priority_score=priority_score,
            status=status,
            is_marked_as_spam=is_marked_as_spam,
            spam_reason=spam_reason,
            complaint_department_id=complaint_department_id,
            submitted_at=current_time,
            updated_at=current_time,
            # ✅ NEW: Image fields
            image_data=image_data,
            image_filename=image_filename,
            image_mimetype=image_mimetype,
            image_size=image_size,
            thumbnail_data=thumbnail_data,
            thumbnail_size=thumbnail_size,
            image_verified=image_verified,
            image_verification_status=image_verification_status
        )
        
        self.session.add(complaint)
        await self.session.commit()
        await self.session.refresh(complaint)
        return complaint
    
    # ==================== READ OPERATIONS ====================
    
    async def get_with_relations(self, complaint_id: UUID) -> Optional[Complaint]:
        """
        Get complaint with all relationships loaded.
        
        Args:
            complaint_id: Complaint UUID
        
        Returns:
            Complaint with relations or None
        """
        query = (
            select(Complaint)
            .options(
                selectinload(Complaint.student),
                selectinload(Complaint.category),
                selectinload(Complaint.assigned_authority),
                selectinload(Complaint.complaint_department),
                selectinload(Complaint.comments),
                selectinload(Complaint.image_verification_logs)  # ✅ ADDED
            )
            .where(Complaint.id == complaint_id)
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def get_by_student(
        self,
        student_roll_no: str,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Complaint]:
        """
        Get complaints by student.
        
        Args:
            student_roll_no: Student roll number
            skip: Number to skip
            limit: Maximum results
            status: Optional status filter
        
        Returns:
            List of complaints
        """
        conditions = [Complaint.student_roll_no == student_roll_no]
        if status:
            conditions.append(Complaint.status == status)
        
        query = (
            select(Complaint)
            .where(and_(*conditions))
            .order_by(desc(Complaint.submitted_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_category(
        self,
        category_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """
        Get complaints by category.
        
        Args:
            category_id: Category ID
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaints
        """
        query = (
            select(Complaint)
            .where(Complaint.category_id == category_id)
            .order_by(desc(Complaint.priority_score))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_status(
        self,
        status: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """
        Get complaints by status.
        
        Args:
            status: Complaint status
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaints
        """
        query = (
            select(Complaint)
            .where(Complaint.status == status)
            .order_by(desc(Complaint.submitted_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_by_priority(
        self,
        priority: str,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """
        Get complaints by priority.
        
        Args:
            priority: Priority level
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaints
        """
        query = (
            select(Complaint)
            .where(Complaint.priority == priority)
            .order_by(desc(Complaint.priority_score))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_assigned_to_authority(
        self,
        authority_id: int,
        skip: int = 0,
        limit: int = 100,
        status: Optional[str] = None
    ) -> List[Complaint]:
        """
        Get complaints assigned to an authority.
        
        Args:
            authority_id: Authority ID
            skip: Number to skip
            limit: Maximum results
            status: Optional status filter
        
        Returns:
            List of complaints
        """
        conditions = [Complaint.assigned_authority_id == authority_id]
        if status:
            conditions.append(Complaint.status == status)
        
        query = (
            select(Complaint)
            .where(and_(*conditions))
            .order_by(desc(Complaint.priority_score))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_public_feed(
        self,
        student_stay_type: str,
        student_department_id: int,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """
        Get public feed filtered by visibility rules.
        
        Args:
            student_stay_type: Student's stay type
            student_department_id: Student's department
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaints
        """
        conditions = [
            Complaint.visibility.in_(["Public", "Department"]),
            Complaint.status != "Closed"
        ]
        
        # Hide hostel complaints from day scholars
        if student_stay_type == "Day Scholar":
            conditions.append(Complaint.category_id != 1)  # 1 = Hostel
        
        # Hide inter-department complaints
        conditions.append(
            or_(
                Complaint.complaint_department_id == student_department_id,
                Complaint.is_cross_department == False
            )
        )
        
        query = (
            select(Complaint)
            .where(and_(*conditions))
            .order_by(desc(Complaint.priority_score))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_high_priority(self, limit: int = 50) -> List[Complaint]:
        """
        Get high priority complaints.
        
        Args:
            limit: Maximum results
        
        Returns:
            List of high priority complaints
        """
        query = (
            select(Complaint)
            .where(
                and_(
                    Complaint.priority.in_(["High", "Critical"]),
                    Complaint.status.in_(["Raised", "In Progress"])
                )
            )
            .order_by(desc(Complaint.priority_score))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_spam_flagged(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """
        Get spam flagged complaints.
        
        Args:
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of spam complaints
        """
        query = (
            select(Complaint)
            .where(Complaint.is_marked_as_spam == True)
            .order_by(desc(Complaint.spam_flagged_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    # ==================== IMAGE-SPECIFIC QUERIES ====================
    
    async def get_with_images(
        self,
        skip: int = 0,
        limit: int = 100,
        verified_only: bool = False
    ) -> List[Complaint]:
        """
        Get complaints that have images attached.
        
        Args:
            skip: Number to skip
            limit: Maximum results
            verified_only: Only return verified images
        
        Returns:
            List of complaints with images
        """
        conditions = [Complaint.image_data.isnot(None)]
        
        if verified_only:
            conditions.append(Complaint.image_verified == True)
        
        query = (
            select(Complaint)
            .where(and_(*conditions))
            .order_by(desc(Complaint.submitted_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_pending_image_verification(
        self,
        limit: int = 50
    ) -> List[Complaint]:
        """
        Get complaints with images pending verification.
        
        Args:
            limit: Maximum results
        
        Returns:
            List of complaints with unverified images
        """
        query = (
            select(Complaint)
            .where(
                and_(
                    Complaint.image_data.isnot(None),
                    Complaint.image_verification_status == "Pending"
                )
            )
            .order_by(desc(Complaint.submitted_at))
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def get_rejected_images(
        self,
        skip: int = 0,
        limit: int = 100
    ) -> List[Complaint]:
        """
        Get complaints with rejected images.
        
        Args:
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaints with rejected images
        """
        query = (
            select(Complaint)
            .where(
                and_(
                    Complaint.image_data.isnot(None),
                    Complaint.image_verification_status == "Rejected"
                )
            )
            .order_by(desc(Complaint.submitted_at))
            .offset(skip)
            .limit(limit)
        )
        result = await self.session.execute(query)
        return result.scalars().all()
    
    async def count_images(self) -> Dict[str, int]:
        """
        Count images by verification status.
        
        Returns:
            Dictionary of image counts
        """
        # Total with images
        total_query = select(func.count(Complaint.id)).where(
            Complaint.image_data.isnot(None)
        )
        total_result = await self.session.execute(total_query)
        total_images = total_result.scalar() or 0
        
        # By verification status
        status_query = (
            select(
                Complaint.image_verification_status,
                func.count(Complaint.id)
            )
            .where(Complaint.image_data.isnot(None))
            .group_by(Complaint.image_verification_status)
        )
        status_result = await self.session.execute(status_query)
        status_counts = dict(status_result.all())
        
        return {
            "total": total_images,
            "verified": status_counts.get("Verified", 0),
            "pending": status_counts.get("Pending", 0),
            "rejected": status_counts.get("Rejected", 0),
            "error": status_counts.get("Error", 0)
        }
    
    # ==================== UPDATE OPERATIONS ====================
    
    async def update_image_verification(
        self,
        complaint_id: UUID,
        is_verified: bool,
        verification_status: str
    ) -> bool:
        """
        Update image verification status.
        
        Args:
            complaint_id: Complaint UUID
            is_verified: Whether image is verified
            verification_status: Verification status (Verified/Rejected/Error)
        
        Returns:
            True if successful
        """
        complaint = await self.get(complaint_id)
        if complaint and complaint.image_data:
            complaint.image_verified = is_verified
            complaint.image_verification_status = verification_status
            complaint.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        return False
    
    async def update_priority_score(
        self,
        complaint_id: UUID,
        new_score: float
    ) -> bool:
        """
        Update complaint priority score.
        
        Args:
            complaint_id: Complaint UUID
            new_score: New priority score
        
        Returns:
            True if successful
        """
        complaint = await self.get(complaint_id)
        if complaint:
            complaint.priority_score = new_score
            
            # Update priority level based on score
            if new_score >= 200:
                complaint.priority = "Critical"
            elif new_score >= 100:
                complaint.priority = "High"
            elif new_score >= 50:
                complaint.priority = "Medium"
            else:
                complaint.priority = "Low"
            
            complaint.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        return False
    
    async def increment_votes(
        self,
        complaint_id: UUID,
        upvote: bool = True
    ) -> bool:
        """
        Increment upvote or downvote count.
        
        Args:
            complaint_id: Complaint UUID
            upvote: True for upvote, False for downvote
        
        Returns:
            True if successful
        """
        complaint = await self.get(complaint_id)
        if complaint:
            if upvote:
                complaint.upvotes += 1
            else:
                complaint.downvotes += 1
            complaint.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        return False
    
    async def decrement_votes(
        self,
        complaint_id: UUID,
        upvote: bool = True
    ) -> bool:
        """
        Decrement upvote or downvote count.
        
        Args:
            complaint_id: Complaint UUID
            upvote: True for upvote, False for downvote
        
        Returns:
            True if successful
        """
        complaint = await self.get(complaint_id)
        if complaint:
            if upvote and complaint.upvotes > 0:
                complaint.upvotes -= 1
            elif not upvote and complaint.downvotes > 0:
                complaint.downvotes -= 1
            complaint.updated_at = datetime.now(timezone.utc)
            await self.session.commit()
            return True
        return False
    
    # ==================== STATISTICS ====================
    
    async def count_by_status(self) -> Dict[str, int]:
        """
        Count complaints by status.
        
        Returns:
            Dictionary of status counts
        """
        query = (
            select(Complaint.status, func.count(Complaint.id))
            .group_by(Complaint.status)
        )
        result = await self.session.execute(query)
        return dict(result.all())
    
    async def count_by_category(self) -> Dict[str, int]:
        """
        Count complaints by category.
        
        Returns:
            Dictionary of category counts
        """
        query = (
            select(ComplaintCategory.name, func.count(Complaint.id))
            .join(Complaint.category)
            .group_by(ComplaintCategory.name)
        )
        result = await self.session.execute(query)
        return dict(result.all())
    
    async def count_by_priority(self) -> Dict[str, int]:
        """
        Count complaints by priority.
        
        Returns:
            Dictionary of priority counts
        """
        query = (
            select(Complaint.priority, func.count(Complaint.id))
            .group_by(Complaint.priority)
        )
        result = await self.session.execute(query)
        return dict(result.all())
    
    async def get_pending_for_escalation(
        self,
        hours: int = 48
    ) -> List[Complaint]:
        """
        Get complaints pending for escalation.
        
        Args:
            hours: Hours threshold for escalation
        
        Returns:
            List of complaints needing escalation
        """
        threshold_time = datetime.now(timezone.utc) - timedelta(hours=hours)
        
        query = (
            select(Complaint)
            .where(
                and_(
                    Complaint.status == "Raised",
                    Complaint.assigned_at < threshold_time
                )
            )
        )
        result = await self.session.execute(query)
        return result.scalars().all()


__all__ = ["ComplaintRepository"]
