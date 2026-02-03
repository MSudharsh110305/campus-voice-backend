"""
Complete database setup script.

Creates tables, seeds initial data, and creates admin user.

✅ FIXED: Use actual table name from database (complaint_categories)
"""

import asyncio
from sqlalchemy import text

from src.database.connection import AsyncSessionLocal, engine
from src.database.models import (
    Base, Department, ComplaintCategory, Authority,
    Student, Complaint, Vote, StatusUpdate, AuthorityUpdate, Notification
)
from src.services.auth_service import auth_service
from src.config.settings import settings

import logging
logger = logging.getLogger(__name__)


async def test_connection():
    """Test database connection."""
    print("🔌 Testing database connection...")
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version()"))
            version = result.scalar()
            print(f"✅ Connected to: {version}")
            return True
    except Exception as e:
        print(f"❌ Connection failed: {e}")
        return False


async def drop_all_tables():
    """Drop all existing tables."""
    print("🗑️  Dropping all existing tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.drop_all)
        print("✅ All tables dropped successfully")
    except Exception as e:
        print(f"⚠️  Error dropping tables: {e}")


async def create_tables():
    """Create all database tables."""
    print("🔨 Creating database tables...")
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
        print("✅ Tables created successfully!")
        
        # Verify tables
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("""
                SELECT table_name 
                FROM information_schema.tables 
                WHERE table_schema = 'public'
                ORDER BY table_name
            """))
            tables = [row[0] for row in result.fetchall()]
            print(f"   Created tables: {', '.join(tables)}")
    except Exception as e:
        print(f"❌ Error creating tables: {e}")
        raise


async def seed_departments():
    """Seed initial departments."""
    print("\n🌱 Seeding departments...")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text("SELECT COUNT(*) FROM departments"))
            count = result.scalar()
            
            if count > 0:
                print(f"⚠️  Departments already exist ({count} records), skipping...")
                return
            
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
            
            for dept in departments:
                await session.refresh(dept)
                print(f"   - {dept.name} (ID: {dept.id}, Code: {dept.code})")
        
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding departments: {e}")
            raise


async def seed_categories():
    """Seed complaint categories."""
    print("\n🌱 Seeding complaint categories...")
    async with AsyncSessionLocal() as session:
        try:
            # ✅ FIXED: Use actual table name from database
            result = await session.execute(text("SELECT COUNT(*) FROM complaint_categories"))
            count = result.scalar()
            
            if count > 0:
                print(f"⚠️  Categories already exist ({count} records), skipping...")
                return
            
            categories = [
                ComplaintCategory(
                    name="Hostel",
                    description="Hostel facilities, room issues, mess complaints, accommodation problems",
                    keywords=["hostel", "room", "mess", "warden", "accommodation", "bed", "bathroom"]
                ),
                ComplaintCategory(
                    name="General",
                    description="Canteen, library, playground, campus facilities, common areas",
                    keywords=["canteen", "library", "playground", "campus", "facility", "ground", "parking"]
                ),
                ComplaintCategory(
                    name="Department",
                    description="Academic issues, lab facilities, classroom problems, faculty concerns",
                    keywords=["department", "lab", "class", "faculty", "academic", "classroom", "equipment"]
                ),
                ComplaintCategory(
                    name="Disciplinary Committee",
                    description="Ragging, harassment, bullying, safety concerns, disciplinary issues",
                    keywords=["ragging", "harassment", "bullying", "safety", "discipline", "threat", "abuse"]
                ),
            ]
            
            for category in categories:
                session.add(category)
            
            await session.commit()
            print(f"✅ Seeded {len(categories)} categories")
            
            for category in categories:
                await session.refresh(category)
                print(f"   - {category.name} (ID: {category.id})")
        
        except Exception as e:
            await session.rollback()
            print(f"❌ Error seeding categories: {e}")
            raise


async def create_admin_user():
    """Create initial admin user."""
    print("\n👤 Creating admin user...")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text("SELECT id FROM authorities WHERE email = :email"),
                {"email": settings.ADMIN_EMAIL}
            )
            existing = result.first()
            
            if existing:
                print(f"⚠️  Admin user already exists (ID: {existing[0]})")
                return
            
            admin = Authority(
                name=settings.ADMIN_NAME,
                email=settings.ADMIN_EMAIL,
                password_hash=auth_service.hash_password(settings.ADMIN_PASSWORD),
                phone=None,
                authority_type="Admin",
                authority_level=100,
                designation="System Administrator",
                is_active=True,
                department_id=None
            )
            
            session.add(admin)
            await session.commit()
            await session.refresh(admin)
            
            print(f"✅ Admin user created successfully")
            print(f"   ID: {admin.id}")
            print(f"   Name: {admin.name}")
            print(f"   Email: {admin.email}")
            print(f"   Authority Level: {admin.authority_level}")
        
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating admin: {e}")
            raise


async def create_sample_authorities():
    """Create sample authorities for testing."""
    print("\n👥 Creating sample authorities...")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(
                text("SELECT COUNT(*) FROM authorities WHERE authority_type != 'Admin'")
            )
            count = result.scalar()
            
            if count > 0:
                print(f"⚠️  Sample authorities already exist ({count} records), skipping...")
                return
            
            authorities = [
                Authority(
                    name="Dr. Rajesh Kumar",
                    email="warden@college.edu",
                    password_hash=auth_service.hash_password("Warden@123"),
                    phone="9876543210",
                    authority_type="Warden",
                    authority_level=5,
                    designation="Chief Warden",
                    is_active=True,
                    department_id=None
                ),
                Authority(
                    name="Prof. Sita Devi",
                    email="hod.cse@college.edu",
                    password_hash=auth_service.hash_password("HOD@123"),
                    phone="9876543211",
                    authority_type="HOD",
                    authority_level=10,
                    designation="Head of Department - CSE",
                    is_active=True,
                    department_id=1
                ),
                Authority(
                    name="Mr. Arun Sharma",
                    email="admin.officer@college.edu",
                    password_hash=auth_service.hash_password("Officer@123"),
                    phone="9876543212",
                    authority_type="Admin Officer",
                    authority_level=7,
                    designation="Senior Administrative Officer",
                    is_active=True,
                    department_id=None
                ),
            ]
            
            for authority in authorities:
                session.add(authority)
            
            await session.commit()
            print(f"✅ Created {len(authorities)} sample authorities")
            
            for authority in authorities:
                await session.refresh(authority)
                print(f"   - {authority.name} ({authority.authority_type})")
                print(f"     Email: {authority.email}")
        
        except Exception as e:
            await session.rollback()
            print(f"❌ Error creating sample authorities: {e}")
            raise


async def verify_schema():
    """Verify database schema includes all required columns."""
    print("\n🔍 Verifying database schema...")
    async with AsyncSessionLocal() as session:
        try:
            result = await session.execute(text("""
                SELECT column_name, data_type, is_nullable, column_default
                FROM information_schema.columns
                WHERE table_name = 'students'
                AND column_name IN ('year', 'roll_no', 'email', 'gender', 'stay_type')
                ORDER BY ordinal_position
            """))
            student_columns = result.fetchall()
            
            print("   Students table key columns:")
            for col in student_columns:
                print(f"   - {col[0]}: {col[1]} (nullable: {col[2]}, default: {col[3]})")
            
            year_exists = any(col[0] == 'year' for col in student_columns)
            if year_exists:
                print("   ✅ Students.year column exists")
            else:
                print("   ❌ Students.year column MISSING!")
            
            result = await session.execute(text("""
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = 'public'
                AND table_name = 'authority_updates'
            """))
            updates_table = result.fetchone()
            
            if updates_table:
                print("   ✅ authority_updates table exists")
            else:
                print("   ⚠️  authority_updates table not found")
        
        except Exception as e:
            print(f"⚠️  Schema verification warning: {e}")


async def print_summary():
    """Print setup summary."""
    print("\n" + "=" * 80)
    print("📊 DATABASE SETUP SUMMARY")
    print("=" * 80)
    
    async with AsyncSessionLocal() as session:
        try:
            # ✅ FIXED: Use actual table names
            tables = {
                "departments": "Departments",
                "complaint_categories": "Complaint Categories",  # ✅ Actual table name
                "authorities": "Authorities",
                "students": "Students",
                "complaints": "Complaints"
            }
            
            for table, label in tables.items():
                result = await session.execute(text(f"SELECT COUNT(*) FROM {table}"))
                count = result.scalar()
                print(f"   {label}: {count} records")
        
        except Exception as e:
            print(f"⚠️  Could not generate summary: {e}")


async def main():
    """Run all setup tasks."""
    print("=" * 80)
    print("🚀 CampusVoice Database Setup")
    print("=" * 80)
    print()
    
    try:
        connected = await test_connection()
        if not connected:
            print("\n❌ Cannot proceed without database connection")
            return
        print()
        
        response = input("⚠️  Drop existing tables? (yes/no): ")
        if response.lower() == "yes":
            await drop_all_tables()
            print()
        
        await create_tables()
        await seed_departments()
        await seed_categories()
        await create_admin_user()
        await create_sample_authorities()
        await verify_schema()
        await print_summary()
        
        print()
        print("=" * 80)
        print("✅ DATABASE SETUP COMPLETE!")
        print("=" * 80)
        print()
        print("📋 Login Credentials:")
        print()
        print("   ADMIN:")
        print(f"   Email: {settings.ADMIN_EMAIL}")
        print(f"   Password: {settings.ADMIN_PASSWORD}")
        print()
        print("   SAMPLE WARDEN:")
        print(f"   Email: warden@college.edu")
        print(f"   Password: Warden@123")
        print()
        print("   SAMPLE HOD (CSE):")
        print(f"   Email: hod.cse@college.edu")
        print(f"   Password: HOD@123")
        print()
        print("⚠️  IMPORTANT: Change all default passwords after first login!")
        print("=" * 80)
    
    except Exception as e:
        print()
        print("=" * 80)
        print(f"❌ Setup failed: {e}")
        print("=" * 80)
        import traceback
        traceback.print_exc()
        raise


if __name__ == "__main__":
    asyncio.run(main())
