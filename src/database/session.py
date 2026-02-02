"""
Database session management.
Async SQLAlchemy engine and session configuration.
"""

import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
)
from sqlalchemy.pool import NullPool

from src.config.settings import settings

logger = logging.getLogger(__name__)


# ==================== CREATE ASYNC ENGINE ====================

def create_database_engine() -> AsyncEngine:
    """
    Create async SQLAlchemy engine with connection pooling.
    
    Returns:
        AsyncEngine instance
    """
    # Engine configuration
    engine_kwargs = {
        "echo": settings.DB_ECHO,
        "future": True,
    }
    
    # For SQLite, use NullPool (no pooling)
    if "sqlite" in settings.DATABASE_URL:
        engine_kwargs["poolclass"] = NullPool
        logger.info("Using NullPool for SQLite")
    else:
        # For PostgreSQL with asyncpg, use default async pooling
        # AsyncPG has its own connection pool
        engine_kwargs.update({
            "pool_size": settings.DB_POOL_SIZE,
            "max_overflow": settings.DB_MAX_OVERFLOW,
            "pool_timeout": settings.DB_POOL_TIMEOUT,
            "pool_recycle": settings.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        })
        logger.info(f"Using connection pool: size={settings.DB_POOL_SIZE}, max_overflow={settings.DB_MAX_OVERFLOW}")
    
    engine = create_async_engine(
        settings.DATABASE_URL,
        **engine_kwargs
    )
    
    db_name = settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'SQLite'
    logger.info(f"Database engine created: {db_name}")
    
    return engine


# Create global engine instance
async_engine: AsyncEngine = create_database_engine()


# ==================== CREATE SESSION MAKER ====================

# Create async session factory
async_session_maker = async_sessionmaker(
    async_engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Don't expire objects after commit
    autocommit=False,
    autoflush=False,
)


# ==================== SESSION DEPENDENCY ====================

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency function to get database session.
    
    Yields:
        AsyncSession: Database session
    
    Usage:
        @router.get("/")
        async def route(db: AsyncSession = Depends(get_db)):
            # Use db here
            pass
    """
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception as e:
            await session.rollback()
            logger.error(f"Database session error: {e}")
            raise
        finally:
            await session.close()


# ==================== ALTERNATIVE: Manual Session ====================

async def get_session() -> AsyncSession:
    """
    Get a database session manually (not for FastAPI dependency).
    Remember to close it after use.
    
    Returns:
        AsyncSession
    
    Usage:
        session = await get_session()
        try:
            # Use session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
    """
    return async_session_maker()


# ==================== DATABASE UTILITIES ====================

async def init_db():
    """
    Initialize database - create all tables.
    
    Usage:
        await init_db()
    """
    from src.database.models import Base
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    
    logger.info("Database tables created successfully")


async def drop_db():
    """
    Drop all database tables.
    
    ⚠️ DANGER: This will delete all data!
    
    Usage:
        await drop_db()
    """
    from src.database.models import Base
    
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
    
    logger.warning("All database tables dropped")


async def reset_db():
    """
    Reset database - drop and recreate all tables.
    
    ⚠️ DANGER: This will delete all data!
    
    Usage:
        await reset_db()
    """
    await drop_db()
    await init_db()
    logger.info("Database reset complete")


async def check_connection():
    """
    Check if database connection is working.
    
    Returns:
        bool: True if connection successful
    
    Usage:
        is_connected = await check_connection()
    """
    try:
        async with async_session_maker() as session:
            from sqlalchemy import text
            await session.execute(text("SELECT 1"))
        logger.info("Database connection successful")
        return True
    except Exception as e:
        logger.error(f"Database connection failed: {e}")
        return False


async def close_db():
    """
    Close database engine and cleanup connections.
    
    Usage:
        await close_db()
    """
    await async_engine.dispose()
    logger.info("Database connections closed")


# ==================== EXPORT ====================

__all__ = [
    "async_engine",
    "async_session_maker",
    "get_db",
    "get_session",
    "init_db",
    "drop_db",
    "reset_db",
    "check_connection",
    "close_db",
]
