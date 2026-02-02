"""
API routes package initialization.
Register all route modules.
"""

from fastapi import APIRouter
from .students import router as students_router
from .complaints import router as complaints_router
from .authorities import router as authorities_router
from .admin import router as admin_router
from .health import router as health_router


def create_api_router() -> APIRouter:
    """
    Create main API router with all sub-routers.
    
    Returns:
        Configured API router
    """
    api_router = APIRouter(prefix="/api")
    
    # Register all routers
    api_router.include_router(students_router)
    api_router.include_router(complaints_router)
    api_router.include_router(authorities_router)
    api_router.include_router(admin_router)
    
    # Health checks at root level (no /api prefix)
    root_router = APIRouter()
    root_router.include_router(health_router)
    
    return api_router, root_router


__all__ = [
    "create_api_router",
    "students_router",
    "complaints_router",
    "authorities_router",
    "admin_router",
    "health_router",
]
