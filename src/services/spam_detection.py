"""
Spam detection service.
"""

import logging
from typing import Dict, Any
from sqlalchemy.ext.asyncio import AsyncSession
from src.repositories.complaint_repo import ComplaintRepository
from src.config.constants import SPAM_KEYWORDS, MIN_COMPLAINT_LENGTH

logger = logging.getLogger(__name__)


class SpamDetectionService:
    """Service for spam detection"""
    
    async def check_spam_blacklist(
        self,
        db: AsyncSession,
        student_roll_no: str
    ) -> Dict[str, Any]:
        """
        Check if student is on spam blacklist.
        
        Args:
            db: Database session
            student_roll_no: Student roll number
        
        Returns:
            Dictionary with is_blacklisted status
        """
        from src.database.models import SpamBlacklist
        from datetime import datetime
        from sqlalchemy import select
        
        query = select(SpamBlacklist).where(
            SpamBlacklist.student_roll_no == student_roll_no
        )
        result = await db.execute(query)
        blacklist = result.scalar_one_or_none()
        
        if not blacklist:
            return {"is_blacklisted": False}
        
        # Check if temporary ban expired
        if not blacklist.is_permanent and blacklist.expires_at:
            if datetime.utcnow() > blacklist.expires_at:
                # Ban expired, remove from blacklist
                await db.delete(blacklist)
                await db.commit()
                return {"is_blacklisted": False}
        
        return {
            "is_blacklisted": True,
            "reason": blacklist.reason,
            "is_permanent": blacklist.is_permanent,
            "expires_at": blacklist.expires_at
        }
    
    def contains_spam_keywords(self, text: str) -> bool:
        """
        Check if text contains spam keywords.
        
        Args:
            text: Text to check
        
        Returns:
            True if contains spam keywords
        """
        text_lower = text.lower()
        return any(keyword in text_lower for keyword in SPAM_KEYWORDS)


# Create global instance
spam_detection_service = SpamDetectionService()

__all__ = ["SpamDetectionService", "spam_detection_service"]
