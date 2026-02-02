"""
Application lifespan management.
Startup and shutdown event handlers.
"""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from src.database import async_engine, async_session_maker
from src.config.settings import settings
from src.utils.logger import app_logger

logger = logging.getLogger(__name__)


async def startup_tasks():
    """
    Execute tasks on application startup.
    
    - Test database connection
    - Create tables if needed
    - Initialize services
    - Warm up LLM service
    """
    app_logger.info("🚀 Starting application...")
    
    # Test database connection
    try:
        async with async_session_maker() as session:
            await session.execute(text("SELECT 1"))
        app_logger.info("✅ Database connection successful")
    except Exception as e:
        app_logger.error(f"❌ Database connection failed: {e}")
        raise
    
    # Create tables (if using SQLite or first run)
    if settings.ENVIRONMENT == "development":
        try:
            from src.database.models import Base
            async with async_engine.begin() as conn:
                # Only create tables if they don't exist
                await conn.run_sync(Base.metadata.create_all)
            app_logger.info("✅ Database tables initialized")
        except Exception as e:
            app_logger.warning(f"⚠️ Table creation skipped: {e}")
    
    # Test LLM service
    try:
        from src.services.llm_service import llm_service
        # Optionally warm up the service with a test call
        app_logger.info("✅ LLM service initialized")
    except Exception as e:
        app_logger.warning(f"⚠️ LLM service initialization warning: {e}")
    
    # Initialize rate limiter
    try:
        from src.utils.rate_limiter import rate_limiter
        app_logger.info("✅ Rate limiter initialized")
    except Exception as e:
        app_logger.warning(f"⚠️ Rate limiter initialization warning: {e}")
    
    app_logger.info("✅ Application startup complete")


async def shutdown_tasks():
    """
    Execute tasks on application shutdown.
    
    - Close database connections
    - Cleanup resources
    - Save state if needed
    """
    app_logger.info("🛑 Shutting down application...")
    
    # Close database connections
    try:
        await async_engine.dispose()
        app_logger.info("✅ Database connections closed")
    except Exception as e:
        app_logger.error(f"❌ Error closing database: {e}")
    
    # Cleanup rate limiter
    try:
        from src.utils.rate_limiter import rate_limiter
        rate_limiter.clear()
        app_logger.info("✅ Rate limiter cleared")
    except Exception as e:
        app_logger.warning(f"⚠️ Rate limiter cleanup warning: {e}")
    
    app_logger.info("✅ Application shutdown complete")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Lifespan context manager for FastAPI application.
    
    Args:
        app: FastAPI application instance
    
    Yields:
        None
    """
    # Startup
    await startup_tasks()
    
    yield
    
    # Shutdown
    await shutdown_tasks()


__all__ = ["lifespan", "startup_tasks", "shutdown_tasks"]
