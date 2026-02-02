"""
Image verification service.
"""

import logging
from typing import Dict, Any
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from src.services.llm_service import llm_service

logger = logging.getLogger(__name__)


class ImageVerificationService:
    """Service for image verification"""
    
    async def verify_image(
        self,
        db: AsyncSession,
        complaint_id: UUID,
        complaint_text: str,
        image_url: str,
        image_description: str = None
    ) -> Dict[str, Any]:
        """
        Verify if image is relevant to complaint.
        
        Args:
            db: Database session
            complaint_id: Complaint UUID
            complaint_text: Complaint text
            image_url: Image URL
            image_description: Optional image description
        
        Returns:
            Verification result
        """
        # Use LLM to verify relevance
        result = await llm_service.verify_image_relevance(
            complaint_text, image_description
        )
        
        # Log verification
        from src.database.models import ImageVerificationLog
        log = ImageVerificationLog(
            complaint_id=complaint_id,
            image_url=image_url,
            is_relevant=result["is_relevant"],
            confidence_score=result["confidence"],
            rejection_reason=result["reason"] if not result["is_relevant"] else None
        )
        db.add(log)
        await db.commit()
        
        logger.info(f"Image verification for {complaint_id}: {result['is_relevant']}")
        
        return result


# Create global instance
image_verification_service = ImageVerificationService()

__all__ = ["ImageVerificationService", "image_verification_service"]
