"""
Authority service for routing and escalation logic.
"""

import logging
from typing import Optional
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.models import Authority
from src.repositories.authority_repo import AuthorityRepository
from src.config.constants import ESCALATION_RULES

logger = logging.getLogger(__name__)


class AuthorityService:
    """Service for authority operations"""
    
    async def route_complaint(
        self,
        db: AsyncSession,
        category_id: int,
        department_id: Optional[int],
        is_against_authority: bool
    ) -> Optional[Authority]:
        """
        Route complaint to appropriate authority.
        
        Args:
            db: Database session
            category_id: Complaint category ID
            department_id: Student's department ID
            is_against_authority: If complaint is against an authority
        
        Returns:
            Authority or None
        """
        authority_repo = AuthorityRepository(db)
        
        # Get category name
        from src.database.models import ComplaintCategory
        category = await db.get(ComplaintCategory, category_id)
        if not category:
            logger.error(f"Category {category_id} not found")
            return None
        
        category_name = category.name
        
        # Route based on category
        if category_name == "Hostel":
            authority = await authority_repo.get_default_for_category("Hostel", None)
        elif category_name == "Department":
            authority = await authority_repo.get_default_for_category("Department", department_id)
        elif category_name == "Disciplinary Committee":
            authority = await authority_repo.get_default_for_category("Disciplinary Committee", None)
        else:  # General
            authority = await authority_repo.get_default_for_category("General", None)
        
        # If complaint is against authority, escalate
        if is_against_authority and authority:
            authority = await self.get_escalated_authority(db, authority.id)
        
        return authority
    
    async def get_escalated_authority(
        self,
        db: AsyncSession,
        current_authority_id: int
    ) -> Optional[Authority]:
        """
        Get higher authority for escalation.
        
        Args:
            db: Database session
            current_authority_id: Current authority ID
        
        Returns:
            Higher authority or None
        """
        authority_repo = AuthorityRepository(db)
        
        current_authority = await authority_repo.get(current_authority_id)
        if not current_authority:
            return None
        
        # Get next authority type from escalation rules
        next_type = ESCALATION_RULES.get(current_authority.authority_type)
        if not next_type:
            return None
        
        # Get authority of next type
        authorities = await authority_repo.get_by_type(next_type)
        return authorities[0] if authorities else None


# Create global instance
authority_service = AuthorityService()

__all__ = ["AuthorityService", "authority_service"]
