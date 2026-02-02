"""
Database migration: Add 'year' column to students table.
"""

import asyncio
from sqlalchemy import text
from src.database.connection import AsyncSessionLocal, engine
from src.utils.logger import app_logger


async def migrate():
    """Add year column to students table."""
    print("=" * 80)
    print("DATABASE MIGRATION: Adding 'year' column to students table")
    print("=" * 80)
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if column already exists
            check_query = text("""
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name = 'students' 
                AND column_name = 'year'
            """)
            
            result = await session.execute(check_query)
            exists = result.scalar()
            
            if exists:
                print("\n✅ Column 'year' already exists in students table")
                return
            
            print("\n1. Adding 'year' column to students table...")
            
            # Add the column with a default value
            alter_query = text("""
                ALTER TABLE students 
                ADD COLUMN year INTEGER DEFAULT 1 NOT NULL
            """)
            
            await session.execute(alter_query)
            await session.commit()
            
            print("   ✅ Column added successfully")
            
            # Verify
            verify_query = text("""
                SELECT column_name, data_type, column_default
                FROM information_schema.columns 
                WHERE table_name = 'students' 
                AND column_name = 'year'
            """)
            
            result = await session.execute(verify_query)
            row = result.fetchone()
            
            if row:
                print(f"\n2. Verification:")
                print(f"   ✅ Column name: {row[0]}")
                print(f"   ✅ Data type: {row[1]}")
                print(f"   ✅ Default value: {row[2]}")
            
            print("\n" + "=" * 80)
            print("✅ Migration completed successfully!")
            print("=" * 80)
            
    except Exception as e:
        print(f"\n❌ Migration failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(migrate())
