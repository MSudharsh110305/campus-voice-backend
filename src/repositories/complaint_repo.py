"""
Complaint repository with specialized queries.
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
                selectinload(Complaint.comments)  # Load comments relationship
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
            await self.session.commit()
            return True
        return False
    
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
