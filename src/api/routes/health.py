"""
Health check endpoints.
"""

import logging
from datetime import datetime
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from src.database.session import get_db
from src.config.settings import settings

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Health"])


@router.get(
    "/health",
    summary="Health check",
    description="Check if API is running"
)
async def health_check():
    """Basic health check endpoint."""
    return {
        "status": "healthy",
        "service": "CampusVoice API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


@router.get(
    "/health/detailed",
    summary="Detailed health check",
    description="Detailed health check with database connectivity"
)
async def detailed_health_check(db: AsyncSession = Depends(get_db)):
    """
    Detailed health check including database connectivity.
    """
    health_status = {
        "status": "healthy",
        "service": "CampusVoice API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat(),
        "checks": {}
    }
    
    # Database check
    try:
        result = await db.execute(text("SELECT 1"))
        result.scalar()
        health_status["checks"]["database"] = {
            "status": "healthy",
            "message": "Database connection successful"
        }
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        health_status["status"] = "unhealthy"
        health_status["checks"]["database"] = {
            "status": "unhealthy",
            "message": str(e)
        }
    
    # Add more checks as needed
    health_status["checks"]["environment"] = {
        "status": "healthy",
        "environment": settings.ENVIRONMENT
    }
    
    return health_status


@router.get(
    "/health/ready",
    summary="Readiness check",
    description="Check if service is ready to accept traffic"
)
async def readiness_check(db: AsyncSession = Depends(get_db)):
    """
    Readiness check for Kubernetes/Docker health probes.
    """
    try:
        # Check database
        await db.execute(text("SELECT 1"))
        
        return {
            "ready": True,
            "timestamp": datetime.utcnow().isoformat()
        }
    except Exception as e:
        logger.error(f"Readiness check failed: {e}")
        return {
            "ready": False,
            "error": str(e),
            "timestamp": datetime.utcnow().isoformat()
        }


@router.get(
    "/health/live",
    summary="Liveness check",
    description="Check if service is alive"
)
async def liveness_check():
    """
    Liveness check for Kubernetes/Docker health probes.
    """
    return {
        "alive": True,
        "timestamp": datetime.utcnow().isoformat()
    }


__all__ = ["router"]
