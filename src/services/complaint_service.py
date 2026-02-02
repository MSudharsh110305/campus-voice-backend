"""
Complaint service with main business logic.
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select  # ✅ ADD THIS IMPORT

from src.database.models import Complaint, Student, ComplaintCategory
from src.repositories.complaint_repo import ComplaintRepository
from src.repositories.student_repo import StudentRepository
from src.services.llm_service import llm_service
from src.services.authority_service import authority_service
from src.services.notification_service import notification_service
from src.config.constants import PRIORITY_SCORES

logger = logging.getLogger(__name__)


class ComplaintService:
    """Service for complaint operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.complaint_repo = ComplaintRepository(db)
        self.student_repo = StudentRepository(db)
    
    async def create_complaint(
        self,
        student_roll_no: str,
        category_id: int,
        original_text: str,
        visibility: str = "Public"
    ) -> Dict[str, Any]:
        """
        Create a new complaint with full LLM processing.
        
        Args:
            student_roll_no: Student roll number
            category_id: Category ID
            original_text: Original complaint text
            visibility: Visibility level
        
        Returns:
            Dictionary with complaint details
        """
        # Get student with department
        student = await self.student_repo.get_with_department(student_roll_no)
        if not student:
            raise ValueError("Student not found")
        
        if not student.is_active:
            raise ValueError("Student account is inactive")
        
        # Check spam blacklist
        # TODO: Implement spam blacklist check
        
        # Build context for LLM
        context = {
            "gender": student.gender,
            "stay_type": student.stay_type,
            "department": student.department.code if student.department else "Unknown"
        }
        
        # LLM Processing
        logger.info(f"Processing complaint for {student_roll_no}")
        
        # 1. Categorize and get priority
        categorization = await llm_service.categorize_complaint(original_text, context)
        
        # 2. Rephrase for professionalism
        rephrased_text = await llm_service.rephrase_complaint(original_text)
        
        # 3. Check for spam
        spam_check = await llm_service.detect_spam(original_text)
        
        # Map category name to ID (if LLM returned name instead of ID)
        if "category" in categorization:
            # ✅ FIXED: Use SQLAlchemy ORM query instead of raw SQL
            category_query = select(ComplaintCategory.id).where(
                ComplaintCategory.name == categorization['category']
            )
            category_result = await self.db.execute(category_query)
            category_row = category_result.first()
            if category_row:
                category_id = category_row[0]
        
        # Calculate initial priority score
        priority = categorization.get("priority", "Medium")
        priority_score = PRIORITY_SCORES.get(priority, 50.0)
        
        # Create complaint
        complaint = await self.complaint_repo.create(
            student_roll_no=student_roll_no,
            category_id=category_id,
            original_text=original_text,
            rephrased_text=rephrased_text,
            visibility=visibility,
            priority=priority,
            priority_score=priority_score,
            status="Raised" if not spam_check.get("is_spam") else "Spam",
            is_marked_as_spam=spam_check.get("is_spam", False),
            spam_reason=spam_check.get("reason") if spam_check.get("is_spam") else None,
            complaint_department_id=student.department_id
        )
        
        # Route to appropriate authority
        authority = None  # ✅ Initialize authority variable
        if not spam_check.get("is_spam"):
            authority = await authority_service.route_complaint(
                self.db,
                category_id,
                student.department_id,
                categorization.get("is_against_authority", False)
            )
            
            if authority:
                complaint.assigned_authority_id = authority.id
                complaint.assigned_at = datetime.utcnow()
                await self.db.commit()
                
                # Create notification for authority
                await notification_service.create_notification(
                    self.db,
                    recipient_type="Authority",
                    recipient_id=str(authority.id),
                    complaint_id=complaint.id,
                    notification_type="complaint_assigned",
                    message=f"New complaint assigned: {rephrased_text[:100]}..."
                )
        
        logger.info(f"Complaint {complaint.id} created successfully")
        
        return {
            "id": str(complaint.id),  # ✅ CHANGED: from "complaint_id" to "id" to match test expectations
            "status": "Submitted" if not spam_check.get("is_spam") else "Flagged as Spam",
            "rephrased_text": rephrased_text,
            "priority": priority,
            "assigned_authority": authority.name if authority and not spam_check.get("is_spam") else None,
            "message": "Complaint submitted successfully" if not spam_check.get("is_spam") 
                      else "Complaint flagged as spam"
        }
    
    async def update_complaint_status(
        self,
        complaint_id: UUID,
        new_status: str,
        authority_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update complaint status (by authority).
        
        Args:
            complaint_id: Complaint UUID
            new_status: New status
            authority_id: Authority making the change
            reason: Optional reason for change
        
        Returns:
            Updated complaint info
        """
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        # Check if authority has permission
        if complaint.assigned_authority_id != authority_id:
            raise PermissionError("Not authorized to update this complaint")
        
        old_status = complaint.status
        complaint.status = new_status
        
        if new_status == "Resolved":
            complaint.resolved_at = datetime.utcnow()
        
        await self.db.commit()
        
        # Create status update record
        from src.database.models import StatusUpdate
        status_update = StatusUpdate(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=authority_id,
            reason=reason
        )
        self.db.add(status_update)
        await self.db.commit()
        
        # Notify student
        await notification_service.create_notification(
            self.db,
            recipient_type="Student",
            recipient_id=complaint.student_roll_no,
            complaint_id=complaint_id,
            notification_type="status_update",
            message=f"Your complaint status changed to '{new_status}'"
        )
        
        logger.info(f"Complaint {complaint_id} status updated: {old_status} → {new_status}")
        
        return {
            "complaint_id": str(complaint_id),
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": datetime.utcnow()
        }
    
    async def get_public_feed(
        self,
        student_roll_no: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Complaint]:
        """
        Get public feed filtered by visibility rules.
        
        Args:
            student_roll_no: Student requesting feed
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaints
        """
        student = await self.student_repo.get_with_department(student_roll_no)
        if not student:
            raise ValueError("Student not found")
        
        return await self.complaint_repo.get_public_feed(
            student_stay_type=student.stay_type,
            student_department_id=student.department_id,
            skip=skip,
            limit=limit
        )


__all__ = ["ComplaintService"]
