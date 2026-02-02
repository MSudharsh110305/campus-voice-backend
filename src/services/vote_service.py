"""
Vote service for voting logic and priority calculation.
"""

import logging
from typing import Dict, Any, List, Optional
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession

from src.database.models import Vote, Complaint
from src.repositories.vote_repo import VoteRepository
from src.repositories.complaint_repo import ComplaintRepository
from src.config.constants import PRIORITY_SCORES, VOTE_IMPACT_MULTIPLIER

logger = logging.getLogger(__name__)


class VoteService:
    """Service for vote operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.vote_repo = VoteRepository(db)
        self.complaint_repo = ComplaintRepository(db)
    
    async def add_vote(
        self,
        complaint_id: UUID,
        student_roll_no: str,
        vote_type: str
    ) -> Dict[str, Any]:
        """
        Add or update vote on a complaint.
        
        Args:
            complaint_id: Complaint UUID
            student_roll_no: Student roll number
            vote_type: Upvote or Downvote
        
        Returns:
            Updated vote counts and priority
        """
        # Validate vote type
        if vote_type not in ["Upvote", "Downvote"]:
            raise ValueError("Invalid vote type. Must be 'Upvote' or 'Downvote'")
        
        # Get complaint
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        # Check if complaint is resolved (optional: disable voting on resolved complaints)
        if complaint.status == "Resolved":
            raise ValueError("Cannot vote on resolved complaints")
        
        # Check if voting on own complaint
        if complaint.student_roll_no == student_roll_no:
            raise ValueError("Cannot vote on your own complaint")
        
        # Check if already voted
        existing_vote = await self.vote_repo.get_by_complaint_and_student(
            complaint_id, student_roll_no
        )
        
        if existing_vote:
            # Update existing vote (change from upvote to downvote or vice versa)
            old_type = existing_vote.vote_type
            
            if old_type == vote_type:
                raise ValueError(f"You have already {vote_type.lower()}d this complaint")
            
            logger.info(f"Updating vote for {student_roll_no}: {old_type} → {vote_type}")
            
            # Decrement old vote
            if old_type == "Upvote":
                await self.complaint_repo.decrement_votes(complaint_id, upvote=True)
            else:
                await self.complaint_repo.decrement_votes(complaint_id, upvote=False)
            
            # Increment new vote
            if vote_type == "Upvote":
                await self.complaint_repo.increment_votes(complaint_id, upvote=True)
            else:
                await self.complaint_repo.increment_votes(complaint_id, upvote=False)
            
            # Update vote record
            existing_vote.vote_type = vote_type
            existing_vote.updated_at = datetime.now(timezone.utc)
            await self.db.commit()
            
            action = "changed"
        else:
            # Create new vote
            await self.vote_repo.create(
                complaint_id=complaint_id,
                student_roll_no=student_roll_no,
                vote_type=vote_type
            )
            
            # Increment vote count
            if vote_type == "Upvote":
                await self.complaint_repo.increment_votes(complaint_id, upvote=True)
            else:
                await self.complaint_repo.increment_votes(complaint_id, upvote=False)
            
            action = "added"
        
        # Recalculate priority
        await self.recalculate_priority(complaint_id)
        
        # Get updated complaint
        complaint = await self.complaint_repo.get(complaint_id)
        
        logger.info(
            f"Vote {action}: {vote_type} by {student_roll_no} on complaint {complaint_id} "
            f"(Upvotes: {complaint.upvotes}, Downvotes: {complaint.downvotes})"
        )
        
        return {
            "complaint_id": str(complaint_id),
            "vote_type": vote_type,
            "action": action,
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "vote_score": complaint.upvotes - complaint.downvotes,
            "priority_score": complaint.priority_score,
            "priority": complaint.priority,
            "message": f"Vote {action} successfully"
        }
    
    async def remove_vote(
        self,
        complaint_id: UUID,
        student_roll_no: str
    ) -> Dict[str, Any]:
        """
        Remove vote from complaint (un-vote).
        
        Args:
            complaint_id: Complaint UUID
            student_roll_no: Student roll number
        
        Returns:
            Updated vote counts
        """
        vote = await self.vote_repo.get_by_complaint_and_student(
            complaint_id, student_roll_no
        )
        
        if not vote:
            raise ValueError("You have not voted on this complaint")
        
        vote_type = vote.vote_type
        
        # Decrement vote count
        if vote_type == "Upvote":
            await self.complaint_repo.decrement_votes(complaint_id, upvote=True)
        else:
            await self.complaint_repo.decrement_votes(complaint_id, upvote=False)
        
        # Delete vote
        await self.vote_repo.delete_vote(complaint_id, student_roll_no)
        
        # Recalculate priority
        await self.recalculate_priority(complaint_id)
        
        # Get updated complaint
        complaint = await self.complaint_repo.get(complaint_id)
        
        logger.info(
            f"Vote removed: {vote_type} by {student_roll_no} on complaint {complaint_id}"
        )
        
        return {
            "complaint_id": str(complaint_id),
            "removed_vote_type": vote_type,
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "vote_score": complaint.upvotes - complaint.downvotes,
            "priority_score": complaint.priority_score,
            "message": "Vote removed successfully"
        }
    
    async def get_user_vote(
        self,
        complaint_id: UUID,
        student_roll_no: str
    ) -> Optional[Dict[str, Any]]:
        """
        Get user's vote on a complaint.
        
        Args:
            complaint_id: Complaint UUID
            student_roll_no: Student roll number
        
        Returns:
            Vote information or None
        """
        vote = await self.vote_repo.get_by_complaint_and_student(
            complaint_id, student_roll_no
        )
        
        if not vote:
            return None
        
        return {
            "complaint_id": str(complaint_id),
            "student_roll_no": student_roll_no,
            "vote_type": vote.vote_type,
            "voted_at": vote.created_at.isoformat(),
            "updated_at": vote.updated_at.isoformat() if vote.updated_at else None
        }
    
    async def recalculate_priority(self, complaint_id: UUID) -> float:
        """
        Recalculate complaint priority based on votes.
        
        Args:
            complaint_id: Complaint UUID
        
        Returns:
            New priority score
        """
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            logger.warning(f"Cannot recalculate priority - complaint {complaint_id} not found")
            return 0.0
        
        # Base priority score from LLM categorization
        base_score = PRIORITY_SCORES.get(complaint.priority, 50.0)
        
        # Calculate vote impact
        vote_score = complaint.upvotes - complaint.downvotes
        vote_impact = vote_score * VOTE_IMPACT_MULTIPLIER
        
        # Calculate final score (ensure it doesn't go negative)
        final_score = max(base_score + vote_impact, 0.0)
        
        # Update priority score in database
        await self.complaint_repo.update_priority_score(complaint_id, final_score)
        
        # Optionally update priority level based on score
        new_priority_level = self._calculate_priority_level(final_score)
        if new_priority_level != complaint.priority:
            complaint.priority = new_priority_level
            await self.db.commit()
            logger.info(f"Priority level updated for {complaint_id}: {new_priority_level}")
        
        logger.info(
            f"Priority recalculated for {complaint_id}: "
            f"Base={base_score}, Votes={vote_score}, Impact={vote_impact}, Final={final_score}"
        )
        
        return final_score
    
    def _calculate_priority_level(self, priority_score: float) -> str:
        """
        Calculate priority level based on score.
        
        Args:
            priority_score: Calculated priority score
        
        Returns:
            Priority level (Low, Medium, High, Critical)
        """
        if priority_score >= 200:
            return "Critical"
        elif priority_score >= 100:
            return "High"
        elif priority_score >= 50:
            return "Medium"
        else:
            return "Low"
    
    async def get_vote_statistics(
        self,
        complaint_id: UUID
    ) -> Dict[str, Any]:
        """
        Get voting statistics for a complaint.
        
        Args:
            complaint_id: Complaint UUID
        
        Returns:
            Vote statistics
        """
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        # Get all votes
        votes = await self.vote_repo.get_votes_by_complaint(complaint_id)
        
        total_votes = len(votes)
        upvotes = complaint.upvotes
        downvotes = complaint.downvotes
        vote_score = upvotes - downvotes
        
        # Calculate percentages
        upvote_percentage = (upvotes / total_votes * 100) if total_votes > 0 else 0
        downvote_percentage = (downvotes / total_votes * 100) if total_votes > 0 else 0
        
        return {
            "complaint_id": str(complaint_id),
            "total_votes": total_votes,
            "upvotes": upvotes,
            "downvotes": downvotes,
            "vote_score": vote_score,
            "upvote_percentage": round(upvote_percentage, 2),
            "downvote_percentage": round(downvote_percentage, 2),
            "priority_score": complaint.priority_score,
            "priority": complaint.priority
        }
    
    async def get_top_voted_complaints(
        self,
        limit: int = 10,
        vote_type: str = "upvote"
    ) -> List[Dict[str, Any]]:
        """
        Get top voted complaints.
        
        Args:
            limit: Maximum number of results
            vote_type: "upvote" or "downvote"
        
        Returns:
            List of top voted complaints
        """
        from sqlalchemy import select, desc
        
        # Build query based on vote type
        if vote_type.lower() == "upvote":
            query = select(Complaint).where(
                Complaint.status != "Spam"
            ).order_by(desc(Complaint.upvotes)).limit(limit)
        else:
            query = select(Complaint).where(
                Complaint.status != "Spam"
            ).order_by(desc(Complaint.downvotes)).limit(limit)
        
        result = await self.db.execute(query)
        complaints = result.scalars().all()
        
        top_complaints = []
        for complaint in complaints:
            top_complaints.append({
                "id": str(complaint.id),
                "rephrased_text": complaint.rephrased_text[:150] + "..." if len(complaint.rephrased_text) > 150 else complaint.rephrased_text,
                "category": complaint.category.name if complaint.category else "Unknown",
                "upvotes": complaint.upvotes,
                "downvotes": complaint.downvotes,
                "vote_score": complaint.upvotes - complaint.downvotes,
                "priority": complaint.priority,
                "status": complaint.status,
                "created_at": complaint.created_at.isoformat()
            })
        
        return top_complaints
    
    async def get_student_voting_history(
        self,
        student_roll_no: str,
        limit: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Get voting history for a student.
        
        Args:
            student_roll_no: Student roll number
            limit: Maximum results
        
        Returns:
            List of votes
        """
        votes = await self.vote_repo.get_votes_by_student(student_roll_no)
        
        history = []
        for vote in votes[:limit]:
            complaint = await self.complaint_repo.get(vote.complaint_id)
            if complaint:
                history.append({
                    "complaint_id": str(vote.complaint_id),
                    "complaint_title": complaint.rephrased_text[:100] + "..." if len(complaint.rephrased_text) > 100 else complaint.rephrased_text,
                    "vote_type": vote.vote_type,
                    "voted_at": vote.created_at.isoformat(),
                    "complaint_status": complaint.status
                })
        
        return history
    
    async def bulk_recalculate_priorities(self) -> Dict[str, Any]:
        """
        Recalculate priorities for all complaints (maintenance task).
        Should be run periodically as a scheduled job.
        
        Returns:
            Recalculation statistics
        """
        from sqlalchemy import select
        
        # Get all non-spam complaints
        query = select(Complaint).where(Complaint.status != "Spam")
        result = await self.db.execute(query)
        complaints = result.scalars().all()
        
        total = len(complaints)
        updated = 0
        errors = 0
        
        logger.info(f"Starting bulk priority recalculation for {total} complaints")
        
        for complaint in complaints:
            try:
                await self.recalculate_priority(complaint.id)
                updated += 1
            except Exception as e:
                logger.error(f"Error recalculating priority for {complaint.id}: {e}")
                errors += 1
        
        logger.info(f"Bulk recalculation complete: {updated} updated, {errors} errors")
        
        return {
            "total_complaints": total,
            "updated": updated,
            "errors": errors,
            "success_rate": (updated / total * 100) if total > 0 else 0
        }


__all__ = ["VoteService"]
