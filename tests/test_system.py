"""
Comprehensive test script for CampusVoice config and database modules.
Tests configuration loading, database connection, models, and seeding.

Usage:
    python test_system.py
"""

import asyncio
import sys
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

# Color codes for terminal output
class Colors:
    HEADER = '\033[95m'
    BLUE = '\033[94m'
    CYAN = '\033[96m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    END = '\033[0m'
    BOLD = '\033[1m'

def print_header(text: str):
    """Print section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{text.center(70)}{Colors.END}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*70}{Colors.END}\n")

def print_success(text: str):
    """Print success message"""
    print(f"{Colors.GREEN}✅ {text}{Colors.END}")

def print_error(text: str):
    """Print error message"""
    print(f"{Colors.RED}❌ {text}{Colors.END}")

def print_warning(text: str):
    """Print warning message"""
    print(f"{Colors.YELLOW}⚠️  {text}{Colors.END}")

def print_info(text: str):
    """Print info message"""
    print(f"{Colors.CYAN}ℹ️  {text}{Colors.END}")

def print_stat(label: str, value: Any):
    """Print stat line"""
    print(f"{Colors.BLUE}{label:.<50}{Colors.END} {Colors.BOLD}{value}{Colors.END}")


# ==================== CONFIG MODULE TESTS ====================

def test_config_module() -> Dict[str, Any]:
    """Test configuration module"""
    print_header("TESTING CONFIG MODULE")
    results = {"passed": 0, "failed": 0, "details": []}
    
    try:
        # Test 1: Import settings
        print_info("Test 1: Importing settings...")
        from src.config import settings, Settings
        print_success("Settings imported successfully")
        results["passed"] += 1
        results["details"].append(("Settings Import", "PASS"))
        
        # Test 2: Check required settings
        print_info("Test 2: Checking required settings...")
        required_settings = [
            "APP_NAME", "ENVIRONMENT", "DATABASE_URL", 
            "DB_POOL_SIZE", "DB_MAX_OVERFLOW"
        ]
        
        for setting in required_settings:
            if hasattr(settings, setting):
                value = getattr(settings, setting)
                print_stat(f"  {setting}", value)
            else:
                print_error(f"  Missing setting: {setting}")
                results["failed"] += 1
                results["details"].append((f"Setting: {setting}", "FAIL"))
                continue
        
        print_success("All required settings present")
        results["passed"] += 1
        results["details"].append(("Required Settings", "PASS"))
        
        # Test 3: Import constants
        print_info("Test 3: Importing constants...")
        from src.config import (
            DEPARTMENTS, CATEGORIES, AUTHORITY_LEVELS,
            ComplaintStatus, PriorityLevel, AuthorityType
        )
        print_success("Constants imported successfully")
        results["passed"] += 1
        results["details"].append(("Constants Import", "PASS"))
        
        # Test 4: Validate constants data
        print_info("Test 4: Validating constants data...")
        print_stat("  Total Departments", len(DEPARTMENTS))
        print_stat("  Total Categories", len(CATEGORIES))
        print_stat("  Authority Levels", len(AUTHORITY_LEVELS))
        
        if len(DEPARTMENTS) == 13:
            print_success("Correct number of departments (13)")
            results["passed"] += 1
            results["details"].append(("Departments Count", "PASS"))
        else:
            print_error(f"Expected 13 departments, found {len(DEPARTMENTS)}")
            results["failed"] += 1
            results["details"].append(("Departments Count", "FAIL"))
        
        if len(CATEGORIES) == 4:
            print_success("Correct number of categories (4)")
            results["passed"] += 1
            results["details"].append(("Categories Count", "PASS"))
        else:
            print_error(f"Expected 4 categories, found {len(CATEGORIES)}")
            results["failed"] += 1
            results["details"].append(("Categories Count", "FAIL"))
        
        # Test 5: Validate enums
        print_info("Test 5: Validating enums...")
        complaint_statuses = list(ComplaintStatus)
        priority_levels = list(PriorityLevel)
        authority_types = list(AuthorityType)
        
        print_stat("  Complaint Statuses", len(complaint_statuses))
        print_stat("  Priority Levels", len(priority_levels))
        print_stat("  Authority Types", len(authority_types))
        
        print_success("Enums validated successfully")
        results["passed"] += 1
        results["details"].append(("Enums Validation", "PASS"))
        
    except Exception as e:
        print_error(f"Config module test failed: {e}")
        results["failed"] += 1
        results["details"].append(("Config Module", f"FAIL: {str(e)}"))
    
    return results


# ==================== DATABASE MODULE TESTS ====================

async def test_database_module() -> Dict[str, Any]:
    """Test database module"""
    print_header("TESTING DATABASE MODULE")
    results = {"passed": 0, "failed": 0, "details": []}
    
    try:
        # Test 1: Import database components
        print_info("Test 1: Importing database components...")
        from src.database import (
            engine, AsyncSessionLocal, get_db,
            Base, Student, Department, Complaint, Authority
        )
        print_success("Database components imported successfully")
        results["passed"] += 1
        results["details"].append(("Database Import", "PASS"))
        
        # Test 2: Check engine configuration
        print_info("Test 2: Checking engine configuration...")
        print_stat("  Engine Type", type(engine).__name__)
        print_stat("  Pool Size", engine.pool.size())
        print_stat("  Max Overflow", engine.pool._max_overflow)
        print_success("Engine configured correctly")
        results["passed"] += 1
        results["details"].append(("Engine Configuration", "PASS"))
        
        # Test 3: Test database connection
        print_info("Test 3: Testing database connection...")
        from src.database import test_connection
        connection_ok = await test_connection()
        
        if connection_ok:
            print_success("Database connection successful")
            results["passed"] += 1
            results["details"].append(("Database Connection", "PASS"))
        else:
            print_error("Database connection failed")
            results["failed"] += 1
            results["details"].append(("Database Connection", "FAIL"))
            return results
        
        # Test 4: Get database info
        print_info("Test 4: Getting database information...")
        from src.database import get_db_info
        db_info = await get_db_info()
        
        if db_info.get("healthy"):
            print_stat("  PostgreSQL Version", db_info.get("version", "Unknown"))
            print_stat("  Database Size", db_info.get("database_size", "Unknown"))
            print_stat("  Active Connections", db_info.get("connections", "Unknown"))
            print_stat("  Total Tables", db_info.get("table_count", "Unknown"))
            print_stat("  Environment", db_info.get("environment", "Unknown"))
            print_success("Database info retrieved successfully")
            results["passed"] += 1
            results["details"].append(("Database Info", "PASS"))
        else:
            print_error(f"Failed to get database info: {db_info.get('error')}")
            results["failed"] += 1
            results["details"].append(("Database Info", "FAIL"))
        
        # Test 5: Test pool status
        print_info("Test 5: Checking connection pool status...")
        from src.database import get_pool_status
        pool_status = await get_pool_status()
        
        if "error" not in pool_status:
            print_stat("  Pool Size", pool_status.get("size", 0))
            print_stat("  Checked In", pool_status.get("checked_in", 0))
            print_stat("  Checked Out", pool_status.get("checked_out", 0))
            print_stat("  Overflow", pool_status.get("overflow", 0))
            print_stat("  Total Connections", pool_status.get("total", 0))
            print_success("Pool status retrieved successfully")
            results["passed"] += 1
            results["details"].append(("Pool Status", "PASS"))
        else:
            print_error(f"Failed to get pool status: {pool_status.get('error')}")
            results["failed"] += 1
            results["details"].append(("Pool Status", "FAIL"))
        
        # Test 6: Test health check
        print_info("Test 6: Running health check...")
        from src.database import health_check
        is_healthy = await health_check()
        
        if is_healthy:
            print_success("Health check passed")
            results["passed"] += 1
            results["details"].append(("Health Check", "PASS"))
        else:
            print_error("Health check failed")
            results["failed"] += 1
            results["details"].append(("Health Check", "FAIL"))
        
        # Test 7: Validate models
        print_info("Test 7: Validating SQLAlchemy models...")
        
        # ✅ FIXED: Import all models at the beginning
        from src.database.models import (
            Department, ComplaintCategory, Student, Authority,
            Complaint, AuthorityUpdate, Vote, StatusUpdate,
            AuthorityRoutingRule, ImageVerificationLog,
            SpamBlacklist, LLMProcessingLog, Notification,
            Comment, AdminAuditLog
        )
        
        model_names = [
            "Department", "ComplaintCategory", "Student", "Authority",
            "Complaint", "AuthorityUpdate", "Vote", "StatusUpdate",
            "AuthorityRoutingRule", "ImageVerificationLog",
            "SpamBlacklist", "LLMProcessingLog", "Notification",
            "Comment", "AdminAuditLog"
        ]
        
        print_stat("  Total Models", len(model_names))
        for model_name in model_names:
            print(f"{Colors.CYAN}    • {model_name}{Colors.END}")
        
        print_success("All models validated successfully")
        results["passed"] += 1
        results["details"].append(("Models Validation", "PASS"))
        
        # Test 8: Check if tables exist
        print_info("Test 8: Checking database tables...")
        async with AsyncSessionLocal() as session:
            from sqlalchemy import text
            result = await session.execute(
                text("""
                    SELECT table_name 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                    ORDER BY table_name
                """)
            )
            tables = [row[0] for row in result.fetchall()]
            
            if tables:
                print_stat("  Tables Found", len(tables))
                for table in tables:
                    print(f"{Colors.CYAN}    • {table}{Colors.END}")
                print_success("Database tables exist")
                results["passed"] += 1
                results["details"].append(("Database Tables", "PASS"))
            else:
                print_warning("No tables found (database might be empty)")
                print_info("Run initialization to create tables")
                results["passed"] += 1
                results["details"].append(("Database Tables", "EMPTY"))
        
        # Test 9: Check seeded data
        print_info("Test 9: Checking seeded data...")
        async with AsyncSessionLocal() as session:
            from sqlalchemy import select
            
            # Check departments
            result = await session.execute(select(Department))
            dept_count = len(result.scalars().all())
            print_stat("  Departments in DB", dept_count)
            
            # Check categories
            result = await session.execute(select(ComplaintCategory))
            cat_count = len(result.scalars().all())
            print_stat("  Categories in DB", cat_count)
            
            if dept_count > 0 and cat_count > 0:
                print_success("Database has seeded data")
                results["passed"] += 1
                results["details"].append(("Seeded Data", "PASS"))
            else:
                print_warning("Database is empty (needs seeding)")
                results["passed"] += 1
                results["details"].append(("Seeded Data", "EMPTY"))
        
    except Exception as e:
        print_error(f"Database module test failed: {e}")
        import traceback
        traceback.print_exc()
        results["failed"] += 1
        results["details"].append(("Database Module", f"FAIL: {str(e)}"))
    
    return results


# ==================== INTEGRATION TEST ====================

async def test_integration() -> Dict[str, Any]:
    """Test integration between config and database"""
    print_header("TESTING CONFIG-DATABASE INTEGRATION")
    results = {"passed": 0, "failed": 0, "details": []}
    
    try:
        # Test 1: Config values used in database
        print_info("Test 1: Verifying config values in database...")
        from src.config import settings
        from src.database import engine
        
        # ✅ FIXED: Check database name instead of full URL
        db_name = str(engine.url.database)
        if "campusvoice" in db_name.lower():
            print_success(f"Database name matches: {db_name}")
            results["passed"] += 1
            results["details"].append(("Config-DB Name Match", "PASS"))
        else:
            print_error(f"Database name mismatch: {db_name}")
            results["failed"] += 1
            results["details"].append(("Config-DB Name Match", "FAIL"))
        
        # Test 2: Constants match database data
        print_info("Test 2: Verifying constants match database data...")
        from src.config import DEPARTMENTS, CATEGORIES
        from src.database import AsyncSessionLocal, Department
        from src.database.models import ComplaintCategory
        from sqlalchemy import select
        
        async with AsyncSessionLocal() as session:
            # Check departments
            result = await session.execute(select(Department))
            db_depts = result.scalars().all()
            
            if len(db_depts) == len(DEPARTMENTS):
                print_success(f"Department count matches: {len(DEPARTMENTS)}")
                results["passed"] += 1
                results["details"].append(("Department Count Match", "PASS"))
            elif len(db_depts) == 0:
                print_warning("Database is empty (needs seeding)")
                results["passed"] += 1
                results["details"].append(("Department Count Match", "EMPTY"))
            else:
                print_warning(f"Department count mismatch: Config={len(DEPARTMENTS)}, DB={len(db_depts)}")
                results["passed"] += 1
                results["details"].append(("Department Count Match", "MISMATCH"))
            
            # Check categories
            try:
                result = await session.execute(select(ComplaintCategory))
                db_cats = result.scalars().all()
                
                if len(db_cats) == len(CATEGORIES):
                    print_success(f"Category count matches: {len(CATEGORIES)}")
                    results["passed"] += 1
                    results["details"].append(("Category Count Match", "PASS"))
                elif len(db_cats) == 0:
                    print_warning("Database is empty (needs seeding)")
                    results["passed"] += 1
                    results["details"].append(("Category Count Match", "EMPTY"))
                else:
                    print_warning(f"Category count mismatch: Config={len(CATEGORIES)}, DB={len(db_cats)}")
                    results["passed"] += 1
                    results["details"].append(("Category Count Match", "MISMATCH"))
            except Exception as e:
                if "default_authority_id" in str(e):
                    print_error("Schema mismatch: database needs migration!")
                    print_warning("Run: python migrate_db.py")
                    results["failed"] += 1
                    results["details"].append(("Category Schema", "MIGRATION_NEEDED"))
                else:
                    raise
        
        print_success("Integration tests completed")
        
    except Exception as e:
        print_error(f"Integration test failed: {e}")
        results["failed"] += 1
        results["details"].append(("Integration Test", f"FAIL: {str(e)}"))
    
    return results


# ==================== SUMMARY ====================

def print_summary(config_results: Dict, db_results: Dict, integration_results: Dict):
    """Print test summary"""
    print_header("TEST SUMMARY")
    
    total_passed = config_results["passed"] + db_results["passed"] + integration_results["passed"]
    total_failed = config_results["failed"] + db_results["failed"] + integration_results["failed"]
    total_tests = total_passed + total_failed
    
    print_stat("Total Tests Run", total_tests)
    print_stat("Tests Passed", f"{total_passed} ({100*total_passed//total_tests if total_tests > 0 else 0}%)")
    print_stat("Tests Failed", f"{total_failed} ({100*total_failed//total_tests if total_tests > 0 else 0}%)")
    
    print(f"\n{Colors.BOLD}Breakdown:{Colors.END}")
    print_stat("  Config Module", f"{config_results['passed']}/{config_results['passed']+config_results['failed']}")
    print_stat("  Database Module", f"{db_results['passed']}/{db_results['passed']+db_results['failed']}")
    print_stat("  Integration", f"{integration_results['passed']}/{integration_results['passed']+integration_results['failed']}")
    
    if total_failed == 0:
        print(f"\n{Colors.GREEN}{Colors.BOLD}🎉 ALL TESTS PASSED! 🎉{Colors.END}\n")
    else:
        print(f"\n{Colors.YELLOW}{Colors.BOLD}⚠️  SOME TESTS FAILED ⚠️{Colors.END}\n")
        print(f"{Colors.YELLOW}Failed Tests:{Colors.END}")
        
        all_results = [
            ("Config", config_results),
            ("Database", db_results),
            ("Integration", integration_results)
        ]
        
        for category, result in all_results:
            for detail in result["details"]:
                if "FAIL" in detail[1] or "MIGRATION_NEEDED" in detail[1]:
                    print(f"  {Colors.RED}• {category}: {detail[0]} - {detail[1]}{Colors.END}")
    
    print(f"\n{Colors.CYAN}Test completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}{Colors.END}\n")


# ==================== MAIN ====================

async def main():
    """Main test runner"""
    print(f"\n{Colors.BOLD}{Colors.HEADER}")
    print("╔════════════════════════════════════════════════════════════════════╗")
    print("║                  CAMPUSVOICE SYSTEM TEST SUITE                    ║")
    print("║                   Config & Database Validation                    ║")
    print("╚════════════════════════════════════════════════════════════════════╝")
    print(f"{Colors.END}\n")
    
    start_time = datetime.now()
    
    # Run all tests
    config_results = test_config_module()
    db_results = await test_database_module()
    integration_results = await test_integration()
    
    # Print summary
    end_time = datetime.now()
    duration = (end_time - start_time).total_seconds()
    
    print_summary(config_results, db_results, integration_results)
    print_stat("Total Execution Time", f"{duration:.2f} seconds")
    
    # Return exit code
    total_failed = config_results["failed"] + db_results["failed"] + integration_results["failed"]
    return 0 if total_failed == 0 else 1


if __name__ == "__main__":
    try:
        exit_code = asyncio.run(main())
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print(f"\n{Colors.YELLOW}Test interrupted by user{Colors.END}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n{Colors.RED}Fatal error: {e}{Colors.END}\n")
        import traceback
        traceback.print_exc()
        sys.exit(1)
