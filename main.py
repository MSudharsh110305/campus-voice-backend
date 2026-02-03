"""
CampusVoice - Campus Complaint Management System
Main application entry point.

FastAPI application with async support, middleware, and comprehensive error handling.

✅ FIXED: Import from src.database.connection
✅ FIXED: Proper lifespan integration
"""

import sys
import uvicorn
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.config.settings import settings
from src.utils.logger import app_logger


def main():
    """
    Main function to run the application.
    """
    app_logger.info("=" * 60)
    app_logger.info("🎓 CampusVoice - Campus Complaint Management System")
    app_logger.info("=" * 60)
    app_logger.info(f"Environment: {settings.ENVIRONMENT}")
    app_logger.info(f"Host: {settings.HOST}")
    app_logger.info(f"Port: {settings.PORT}")
    app_logger.info(f"Debug Mode: {settings.DEBUG}")
    app_logger.info(f"Workers: {settings.WORKERS}")
    app_logger.info(f"Database: PostgreSQL" if "postgresql" in settings.DATABASE_URL else "SQLite")
    app_logger.info("=" * 60)
    
    # Run with Uvicorn
    uvicorn.run(
        "src.api:app",  # ✅ Correct: uses lifespan from src.api.__init__.py
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        workers=settings.WORKERS if not settings.DEBUG else 1,
        log_level=settings.LOG_LEVEL.lower(),
        access_log=True,
        use_colors=True,
        loop="asyncio",
    )


if __name__ == "__main__":
    main()
