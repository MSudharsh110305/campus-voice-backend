"""
Pydantic schemas for Vote endpoints.
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from uuid import UUID
from src.config.constants import VoteType


class VoteCreate(BaseModel):
    """Schema for creating a vote"""
    
    vote_type: VoteType = Field(
        ...,
        description="Vote type: Upvote or Downvote"
    )
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "vote_type": "Upvote"
            }
        }
    }


class VoteResponse(BaseModel):
    """Schema for vote response"""
    
    complaint_id: UUID
    upvotes: int
    downvotes: int
    priority_score: float
    priority: str
    user_vote: Optional[str] = None  # Current user's vote
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "complaint_id": "123e4567-e89b-12d3-a456-426614174000",
                "upvotes": 15,
                "downvotes": 2,
                "priority_score": 51.3,
                "priority": "Medium",
                "user_vote": "Upvote"
            }
        }
    }


class VoteStats(BaseModel):
    """Schema for vote statistics"""
    
    total_votes: int
    upvotes: int
    downvotes: int
    net_votes: int
    vote_ratio: float  # upvotes / total_votes
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "total_votes": 20,
                "upvotes": 15,
                "downvotes": 5,
                "net_votes": 10,
                "vote_ratio": 0.75
            }
        }
    }


class VoteDeleteResponse(BaseModel):
    """Schema for vote deletion response"""
    
    message: str
    complaint_id: UUID
    upvotes: int
    downvotes: int
    priority_score: float
    
    model_config = {
        "json_schema_extra": {
            "example": {
                "message": "Vote removed successfully",
                "complaint_id": "123e4567-e89b-12d3-a456-426614174000",
                "upvotes": 14,
                "downvotes": 2,
                "priority_score": 51.2
            }
        }
    }


__all__ = [
    "VoteCreate",
    "VoteResponse",
    "VoteStats",
    "VoteDeleteResponse",
]
