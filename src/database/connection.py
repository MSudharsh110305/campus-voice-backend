"""
Database connection management with async support.
Handles engine creation, session management, and database initialization.
"""

import logging
from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool, QueuePool
from sqlalchemy import text, event
from src.config.settings import settings

logger = logging.getLogger(__name__)


# ==================== ENGINE CREATION ====================

def create_engine() -> AsyncEngine:
    """
    Create async database engine with connection pooling.
    
    Returns:
        AsyncEngine: Configured async database engine
    """
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DB_ECHO,
        pool_size=settings.DB_POOL_SIZE,
        max_overflow=settings.DB_MAX_OVERFLOW,
        pool_pre_ping=True,  # Verify connections before using
        pool_recycle=3600,   # Recycle connections after 1 hour
        connect_args={
            "server_settings": {
                "application_name": "CampusVoice",
                "jit": "off",  # Disable JIT for faster simple queries
            },
            "command_timeout": 60,
            "timeout": 30,
        },
    )
    
    logger.info(
        f"Database engine created: pool_size={settings.DB_POOL_SIZE}, "
        f"max_overflow={settings.DB_MAX_OVERFLOW}"
    )
    
    return engine


# Create global engine instance
engine: AsyncEngine = create_engine()


# ==================== SESSION FACTORY ====================

# Create async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autoflush=False,         # Manual control over flushes
    autocommit=False,        # Explicit transaction control
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Usage:
        @app.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            ...
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# ==================== DATABASE INITIALIZATION ====================

async def create_all_tables():
    """
    Create all database tables from SQLAlchemy models.
    Called during application startup.
    """
    from src.database.models import Base
    
    try:
        async with engine.begin() as conn:
            # Drop all tables (use with caution in production!)
            # await conn.run_sync(Base.metadata.drop_all)
            
            # Create all tables
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}")
        raise


async def drop_all_tables():
    """
    Drop all database tables.
    ⚠️ WARNING: Use only in development/testing!
    """
    from src.database.models import Base
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("⚠️ All database tables dropped")
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}")
        raise


async def init_db():
    """
    Initialize database with tables and seed data.
    Called during application startup.
    """
    logger.info("Initializing database...")
    
    try:
        # Create tables
        await create_all_tables()
        
        # Check if database is empty
        async with AsyncSessionLocal() as session:
            from src.database.models import Department
            result = await session.execute(text("SELECT COUNT(*) FROM departments"))
            count = result.scalar()
            
            if count == 0:
                logger.info("Database is empty, seeding initial data...")
                await seed_initial_data(session)
        
        logger.info("✅ Database initialization complete")
    except Exception as e:
        logger.error(f"❌ Database initialization failed: {e}")
        raise


async def seed_initial_data(session: AsyncSession):
    """
    Seed initial data (departments and categories).
    
    Args:
        session: Database session
    """
    from src.database.models import Department, ComplaintCategory
    from src.config.constants import DEPARTMENTS, CATEGORIES
    
    try:
        # Seed departments
        for dept_data in DEPARTMENTS:
            dept = Department(
                code=dept_data["code"],
                name=dept_data["name"],
                hod_name=dept_data.get("hod_name"),
                hod_email=dept_data.get("hod_email"),
            )
            session.add(dept)
        
        # Seed categories
        for cat_data in CATEGORIES:
            category = ComplaintCategory(
                name=cat_data["name"],
                description=cat_data["description"],
            )
            session.add(category)
        
        await session.commit()
        logger.info("✅ Initial data seeded successfully")
    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Failed to seed initial data: {e}")
        raise


# ==================== DATABASE HEALTH CHECK ====================

async def health_check() -> bool:
    """
    Check database connectivity.
    
    Returns:
        bool: True if database is healthy, False otherwise
    """
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


async def get_db_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database info including version, pool status, etc.
    """
    try:
        async with AsyncSessionLocal() as session:
            # Get PostgreSQL version
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            
            # Get connection count
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
            )
            connections = result.scalar()
            
            # Get database size
            result = await session.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            db_size = result.scalar()
            
            return {
                "healthy": True,
                "version": version.split(",")[0] if version else "Unknown",
                "connections": connections,
                "database_size": db_size,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
            }
    except Exception as e:
        logger.error(f"Failed to get database info: {e}")
        return {
            "healthy": False,
            "error": str(e)
        }


# ==================== CLEANUP ====================

async def close_db():
    """
    Close database connections.
    Called during application shutdown.
    """
    try:
        await engine.dispose()
        logger.info("✅ Database connections closed")
    except Exception as e:
        logger.error(f"❌ Failed to close database connections: {e}")


# ==================== TRANSACTION HELPER ====================

async def execute_in_transaction(session: AsyncSession, func, *args, **kwargs):
    """
    Execute a function within a database transaction.
    
    Args:
        session: Database session
        func: Async function to execute
        *args: Function arguments
        **kwargs: Function keyword arguments
    
    Returns:
        Result of the function
    """
    try:
        result = await func(session, *args, **kwargs)
        await session.commit()
        return result
    except Exception as e:
        await session.rollback()
        logger.error(f"Transaction failed: {e}")
        raise


# ==================== EXPORT ====================

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "create_all_tables",
    "drop_all_tables",
    "init_db",
    "health_check",
    "get_db_info",
    "close_db",
    "execute_in_transaction",
]
