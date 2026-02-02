# setup_database.py
"""
Initialize database with tables and seed data.
"""

import asyncio
from sqlalchemy import text
from src.database.session import async_engine, async_session_maker
from src.database.models import Base, Department, ComplaintCategory
from src.services.auth_service import auth_service
from src.config.settings import settings

async def create_tables():
    """Create all database tables."""
    print("🔨 Creating database tables...")
    async with async_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    print("✅ Tables created successfully!")

async def seed_departments():
    """Seed initial departments."""
    print("🌱 Seeding departments...")
    async with async_session_maker() as session:
        departments = [
            Department(name="Computer Science & Engineering", code="CSE"),
            Department(name="Electronics & Communication Engineering", code="ECE"),
            Department(name="Mechanical Engineering", code="MECH"),
            Department(name="Civil Engineering", code="CIVIL"),
            Department(name="Information Technology", code="IT"),
        ]
        
        for dept in departments:
            session.add(dept)
        
        await session.commit()
        print(f"✅ Seeded {len(departments)} departments")

async def seed_categories():
    """Seed complaint categories."""
    print("🌱 Seeding complaint categories...")
    async with async_session_maker() as session:
        categories = [
            ComplaintCategory(
                name="Hostel",
                description="Hostel facilities, room issues, mess complaints",
                keywords=["hostel", "room", "mess", "warden", "accommodation"]
            ),
            ComplaintCategory(
                name="General",
                description="Canteen, library, playground, campus facilities",
                keywords=["canteen", "library", "playground", "campus", "facility"]
            ),
            ComplaintCategory(
                name="Department",
                description="Academic issues, lab facilities, faculty concerns",
                keywords=["department", "lab", "class", "faculty", "academic"]
            ),
            ComplaintCategory(
                name="Disciplinary Committee",
                description="Ragging, harassment, bullying, safety concerns",
                keywords=["ragging", "harassment", "bullying", "safety", "discipline"]
            ),
        ]
        
        for category in categories:
            session.add(category)
        
        await session.commit()
        print(f"✅ Seeded {len(categories)} categories")

async def create_admin_user():
    """Create initial admin user."""
    print("👤 Creating admin user...")
    
    from src.database.models import Authority
    
    async with async_session_maker() as session:
        # Check if admin exists
        result = await session.execute(
            text("SELECT id FROM authorities WHERE email = :email"),
            {"email": settings.ADMIN_EMAIL}
        )
        
        if result.first():
            print("⚠️  Admin user already exists")
            return
        
        admin = Authority(
            name=settings.ADMIN_NAME,
            email=settings.ADMIN_EMAIL,
            password_hash=auth_service.hash_password(settings.ADMIN_PASSWORD),
            authority_type="Admin",
            authority_level=100,
            designation="System Administrator",
            is_active=True
        )
        
        session.add(admin)
        await session.commit()
        print(f"✅ Admin user created: {settings.ADMIN_EMAIL}")

async def test_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    try:
        async with async_session_maker() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to: {version}")
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        raise

async def main():
    """Run all setup tasks."""
    print("=" * 60)
    print("🚀 CampusVoice Database Setup")
    print("=" * 60)
    print()
    
    try:
        await test_connection()
        await create_tables()
        await seed_departments()
        await seed_categories()
        await create_admin_user()
        
        print()
        print("=" * 60)
        print("✅ Database setup complete!")
        print("=" * 60)
        print()
        print("📋 Login Credentials:")
        print(f"   Email: {settings.ADMIN_EMAIL}")
        print(f"   Password: {settings.ADMIN_PASSWORD}")
        print()
        print("⚠️  Change admin password after first login!")
        print("=" * 60)
        
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ Setup failed: {e}")
        print("=" * 60)
        raise

if __name__ == "__main__":
    asyncio.run(main())
