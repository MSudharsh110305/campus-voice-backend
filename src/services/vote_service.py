"""
Vote service for voting logic and priority calculation.
"""

import logging
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Vote
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
    ) -> dict:
        """
        Add or update vote on a complaint.
        
        Args:
            complaint_id: Complaint UUID
            student_roll_no: Student roll number
            vote_type: Upvote or Downvote
        
        Returns:
            Updated vote counts and priority
        """
        # Check if already voted
        existing_vote = await self.vote_repo.get_by_complaint_and_student(
            complaint_id, student_roll_no
        )
        
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        if existing_vote:
            # Update existing vote
            old_type = existing_vote.vote_type
            
            if old_type == vote_type:
                raise ValueError("Already voted with same type")
            
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
            await self.db.commit()
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
        
        # Recalculate priority
        await self.recalculate_priority(complaint_id)
        
        # Get updated complaint
        complaint = await self.complaint_repo.get(complaint_id)
        
        logger.info(f"Vote {vote_type} added for complaint {complaint_id}")
        
        return {
            "complaint_id": str(complaint_id),
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "priority_score": complaint.priority_score,
            "priority": complaint.priority
        }
    
    async def remove_vote(
        self,
        complaint_id: UUID,
        student_roll_no: str
    ) -> dict:
        """
        Remove vote from complaint.
        
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
            raise ValueError("Vote not found")
        
        # Decrement vote count
        if vote.vote_type == "Upvote":
            await self.complaint_repo.decrement_votes(complaint_id, upvote=True)
        else:
            await self.complaint_repo.decrement_votes(complaint_id, upvote=False)
        
        # Delete vote
        await self.vote_repo.delete_vote(complaint_id, student_roll_no)
        
        # Recalculate priority
        await self.recalculate_priority(complaint_id)
        
        complaint = await self.complaint_repo.get(complaint_id)
        
        return {
            "complaint_id": str(complaint_id),
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "priority_score": complaint.priority_score
        }
    
    async def recalculate_priority(self, complaint_id: UUID):
        """
        Recalculate complaint priority based on votes.
        
        Args:
            complaint_id: Complaint UUID
        """
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            return
        
        # Base priority score
        base_score = PRIORITY_SCORES.get(complaint.priority, 50.0)
        
        # Vote impact
        vote_impact = (complaint.upvotes - complaint.downvotes) * VOTE_IMPACT_MULTIPLIER
        
        # Calculate final score
        final_score = base_score + vote_impact
        
        # Update priority score
        await self.complaint_repo.update_priority_score(complaint_id, final_score)
        
        logger.info(f"Priority recalculated for {complaint_id}: {final_score}")


__all__ = ["VoteService"]
