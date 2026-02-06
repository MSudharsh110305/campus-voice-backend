"""
Database connection management with async support.
Handles engine creation, session management, and database initialization.
"""

import logging
import asyncio
from typing import AsyncGenerator, Optional, Callable, Any
from sqlalchemy.ext.asyncio import (
    create_async_engine,
    AsyncSession,
    AsyncEngine,
    async_sessionmaker,
)
from sqlalchemy import text, event
from sqlalchemy.exc import OperationalError, DatabaseError
from src.config.settings import settings

logger = logging.getLogger(__name__)


# ==================== ENGINE CREATION ====================

def create_engine() -> AsyncEngine:
    """
    Create async database engine with connection pooling.
    
    Returns:
        AsyncEngine: Configured async database engine
    
    Raises:
        ValueError: If DATABASE_URL is invalid
    
    Note:
        For async engines, SQLAlchemy automatically uses async-compatible pooling.
    """
    try:
        engine = create_async_engine(
            settings.DATABASE_URL,
            echo=settings.DB_ECHO,
            pool_size=settings.DB_POOL_SIZE,
            max_overflow=settings.DB_MAX_OVERFLOW,
            pool_pre_ping=True,
            pool_recycle=settings.DB_POOL_RECYCLE,
            pool_timeout=settings.DB_POOL_TIMEOUT,
            connect_args={
                "server_settings": {
                    "application_name": settings.APP_NAME,
                    "jit": "off",
                },
                "command_timeout": 60,
                "timeout": 30,
            },
        )
        
        logger.info(
            f"✅ Database engine created: "
            f"pool_size={settings.DB_POOL_SIZE}, "
            f"max_overflow={settings.DB_MAX_OVERFLOW}, "
            f"pool_recycle={settings.DB_POOL_RECYCLE}s, "
            f"environment={settings.ENVIRONMENT}"
        )
        
        return engine
    
    except Exception as e:
        logger.error(f"❌ Failed to create database engine: {e}")
        raise


engine: AsyncEngine = create_engine()


# ==================== CONNECTION EVENT LISTENERS ====================

@event.listens_for(engine.sync_engine, "connect")
def receive_connect(dbapi_conn, connection_record):
    """Log new database connections"""
    if settings.DB_ECHO:
        logger.debug(f"🔌 New database connection established: {id(dbapi_conn)}")


@event.listens_for(engine.sync_engine, "checkout")
def receive_checkout(dbapi_conn, connection_record, connection_proxy):
    """Log connection checkout from pool"""
    if settings.DB_ECHO:
        logger.debug(f"📤 Connection checked out from pool: {id(dbapi_conn)}")


@event.listens_for(engine.sync_engine, "checkin")
def receive_checkin(dbapi_conn, connection_record):
    """Log connection return to pool"""
    if settings.DB_ECHO:
        logger.debug(f"📥 Connection returned to pool: {id(dbapi_conn)}")


# ==================== SESSION FACTORY ====================

AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
    autocommit=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency to get database session.
    
    Usage:
        ```python
        from fastapi import Depends
        from src.database.connection import get_db
        
        @app.get("/users")
        async def get_users(db: AsyncSession = Depends(get_db)):
            result = await db.execute(select(User))
            return result.scalars().all()
        ```
    
    Yields:
        AsyncSession: Database session
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error(f"❌ Database session error: {e}", exc_info=True)
            raise


# ==================== DATABASE INITIALIZATION ====================

async def create_all_tables():
    """
    Create all database tables from SQLAlchemy models.
    Called during application startup.
    """
    from src.database.models import Base
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        
        logger.info("✅ Database tables created successfully")
    
    except Exception as e:
        logger.error(f"❌ Failed to create database tables: {e}", exc_info=True)
        raise


async def drop_all_tables():
    """
    Drop all database tables.
    
    ⚠️ WARNING: Use only in development/testing!
    """
    if settings.is_production:
        raise RuntimeError("❌ Cannot drop tables in production environment!")
    
    from src.database.models import Base
    
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        
        logger.warning("⚠️ All database tables dropped")
    
    except Exception as e:
        logger.error(f"❌ Failed to drop database tables: {e}", exc_info=True)
        raise


async def init_db(retry_attempts: int = 3, retry_delay: int = 5):
    """
    Initialize database with tables and seed data.
    Called during application startup.
    
    Args:
        retry_attempts: Number of retry attempts on failure
        retry_delay: Delay between retries in seconds
    """
    logger.info("🔄 Initializing database...")
    
    for attempt in range(1, retry_attempts + 1):
        try:
            await create_all_tables()
            
            async with AsyncSessionLocal() as session:
                from src.database.models import Department
                
                result = await session.execute(text("SELECT COUNT(*) FROM departments"))
                count = result.scalar()
                
                if count == 0:
                    logger.info("📦 Database is empty, seeding initial data...")
                    await seed_initial_data(session)
                else:
                    logger.info(f"✅ Database already contains {count} departments")
                    # Still seed authorities if missing
                    await seed_authorities(session)

            logger.info("✅ Database initialization complete")
            return
        
        except OperationalError as e:
            if attempt < retry_attempts:
                logger.warning(
                    f"⚠️ Database initialization attempt {attempt}/{retry_attempts} failed. "
                    f"Retrying in {retry_delay}s... Error: {e}"
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(f"❌ Database initialization failed after {retry_attempts} attempts: {e}")
                raise
        
        except Exception as e:
            logger.error(f"❌ Database initialization failed: {e}", exc_info=True)
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
        for dept_data in DEPARTMENTS:
            dept = Department(
                code=dept_data["code"],
                name=dept_data["name"],
                hod_name=dept_data.get("hod_name"),
                hod_email=dept_data.get("hod_email"),
            )
            session.add(dept)
        
        logger.info(f"✅ Added {len(DEPARTMENTS)} departments")
        
        for cat_data in CATEGORIES:
            category = ComplaintCategory(
                name=cat_data["name"],
                description=cat_data["description"],
                keywords=cat_data.get("keywords", []),
            )
            session.add(category)
        
        logger.info(f"✅ Added {len(CATEGORIES)} complaint categories")
        
        await session.commit()
        logger.info("✅ Initial data seeded successfully")

        # Seed default authorities
        await seed_authorities(session)

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Failed to seed initial data: {e}", exc_info=True)
        raise


async def seed_authorities(session: AsyncSession):
    """Seed default authority accounts for testing."""
    from src.database.models import Authority
    from src.services.auth_service import auth_service

    try:
        result = await session.execute(text("SELECT COUNT(*) FROM authorities"))
        count = result.scalar()
        if count and count > 0:
            logger.info(f"✅ Authorities already seeded ({count} found)")
            return

        authorities = [
            {
                "name": "Admin User",
                "email": "admin@campusvoice.edu",
                "password": "Admin@123456",
                "authority_type": "Admin",
                "authority_level": 100,
                "designation": "System Administrator",
                "department_id": None,
            },
            {
                "name": "Dr. Rajesh Kumar",
                "email": "warden@campusvoice.edu",
                "password": "Warden@12345",
                "authority_type": "Warden",
                "authority_level": 5,
                "designation": "Chief Warden",
                "department_id": None,
            },
            {
                "name": "Dr. Priya Sharma",
                "email": "hod.cse@campusvoice.edu",
                "password": "HodCse@12345",
                "authority_type": "HOD",
                "authority_level": 8,
                "designation": "Head of Department - CSE",
                "department_id": 1,
            },
            {
                "name": "Mr. Suresh Reddy",
                "email": "officer@campusvoice.edu",
                "password": "Officer@1234",
                "authority_type": "Admin Officer",
                "authority_level": 50,
                "designation": "Administrative Officer",
                "department_id": None,
            },
            {
                "name": "Dr. Anand Verma",
                "email": "dc@campusvoice.edu",
                "password": "Discip@12345",
                "authority_type": "Disciplinary Committee",
                "authority_level": 20,
                "designation": "Disciplinary Committee Chair",
                "department_id": None,
            },
        ]

        for auth_data in authorities:
            password = auth_data.pop("password")
            auth_data["password_hash"] = auth_service.hash_password(password)
            authority = Authority(**auth_data)
            session.add(authority)

        await session.commit()
        logger.info(f"✅ Seeded {len(authorities)} default authorities")

    except Exception as e:
        await session.rollback()
        logger.error(f"❌ Failed to seed authorities: {e}", exc_info=True)


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
        logger.error(f"❌ Database health check failed: {e}")
        return False


async def get_db_info() -> dict:
    """
    Get database connection information.
    
    Returns:
        dict: Database info including version, pool status, etc.
    """
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            
            result = await session.execute(
                text("SELECT count(*) FROM pg_stat_activity WHERE datname = current_database()")
            )
            connections = result.scalar()
            
            result = await session.execute(
                text("SELECT pg_size_pretty(pg_database_size(current_database()))")
            )
            db_size = result.scalar()
            
            result = await session.execute(
                text("""
                    SELECT count(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
            )
            table_count = result.scalar()
            
            return {
                "healthy": True,
                "version": version.split(",")[0] if version else "Unknown",
                "connections": connections,
                "database_size": db_size,
                "table_count": table_count,
                "pool_size": settings.DB_POOL_SIZE,
                "max_overflow": settings.DB_MAX_OVERFLOW,
                "pool_recycle": settings.DB_POOL_RECYCLE,
                "pool_timeout": settings.DB_POOL_TIMEOUT,
                "environment": settings.ENVIRONMENT,
            }
    
    except Exception as e:
        logger.error(f"❌ Failed to get database info: {e}", exc_info=True)
        return {"healthy": False, "error": str(e)}


async def get_pool_status() -> dict:
    """
    Get connection pool status.
    
    Returns:
        dict: Pool statistics
    """
    try:
        pool = engine.pool
        
        return {
            "size": pool.size(),
            "checked_in": pool.checkedin(),
            "checked_out": pool.checkedout(),
            "overflow": pool.overflow(),
            "total": pool.size() + pool.overflow(),
        }
    
    except Exception as e:
        logger.error(f"❌ Failed to get pool status: {e}")
        return {"error": str(e)}


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
        logger.error(f"❌ Failed to close database connections: {e}", exc_info=True)


# ==================== TRANSACTION HELPERS ====================

async def execute_in_transaction(
    session: AsyncSession, 
    func: Callable, 
    *args, 
    **kwargs
) -> Any:
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
        logger.error(f"❌ Transaction failed: {e}", exc_info=True)
        raise


async def execute_with_retry(
    func: Callable,
    *args,
    max_retries: int = 3,
    retry_delay: float = 1.0,
    **kwargs
) -> Any:
    """
    Execute a database operation with retry logic.
    
    Args:
        func: Async function to execute
        *args: Function arguments
        max_retries: Maximum number of retry attempts
        retry_delay: Delay between retries in seconds
        **kwargs: Function keyword arguments
    
    Returns:
        Result of the function
    """
    last_exception = None
    
    for attempt in range(1, max_retries + 1):
        try:
            return await func(*args, **kwargs)
        
        except (OperationalError, DatabaseError) as e:
            last_exception = e
            if attempt < max_retries:
                logger.warning(
                    f"⚠️ Database operation failed (attempt {attempt}/{max_retries}). "
                    f"Retrying in {retry_delay}s... Error: {e}"
                )
                await asyncio.sleep(retry_delay)
            else:
                logger.error(
                    f"❌ Database operation failed after {max_retries} attempts: {e}",
                    exc_info=True
                )
    
    raise last_exception


# ==================== TESTING HELPERS ====================

async def test_connection():
    """
    Test database connection.
    
    Returns:
        bool: True if connection successful
    """
    try:
        logger.info("🔍 Testing database connection...")
        
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT current_database(), current_user"))
            db_name, db_user = result.fetchone()
            
            logger.info(f"✅ Connected to database '{db_name}' as user '{db_user}'")
        
        return True
    
    except Exception as e:
        logger.error(f"❌ Database connection test failed: {e}", exc_info=True)
        return False


async def reset_database():
    """
    Reset database (drop and recreate tables with seed data).
    
    ⚠️ WARNING: Use only in development/testing!
    """
    if settings.is_production:
        raise RuntimeError("❌ Cannot reset database in production!")
    
    logger.warning("⚠️ Resetting database...")
    
    await drop_all_tables()
    await create_all_tables()
    
    async with AsyncSessionLocal() as session:
        await seed_initial_data(session)
    
    logger.info("✅ Database reset complete")


# ==================== EXPORT ====================

__all__ = [
    "engine",
    "AsyncSessionLocal",
    "get_db",
    "create_all_tables",
    "drop_all_tables",
    "init_db",
    "seed_initial_data",
    "health_check",
    "get_db_info",
    "get_pool_status",
    "test_connection",
    "close_db",
    "execute_in_transaction",
    "execute_with_retry",
    "reset_database",
]
