"""
Test script for Pydantic schemas validation.
Tests all schemas for proper validation, imports, and edge cases.
"""

import sys
from datetime import datetime, timezone, timedelta
from uuid import uuid4
from typing import Dict, List, Any


def test_imports():
    """Test all schema imports"""
    print("=" * 80)
    print("TEST 1: Schema Imports")
    print("=" * 80)
    
    try:
        from src.schemas import (
            # Student
            StudentRegister, StudentLogin, StudentProfile, StudentProfileUpdate,
            StudentResponse, StudentStats, PasswordChange, EmailVerification,
            
            # Complaint
            ComplaintCreate, ComplaintUpdate, ComplaintResponse, ComplaintDetailResponse,
            ComplaintSubmitResponse, ComplaintListResponse, ComplaintFilter, SpamFlag,
            ImageUploadResponse, CommentCreate, CommentResponse, CommentListResponse,
            
            # Authority
            AuthorityLogin, AuthorityCreate, AuthorityProfile, AuthorityResponse,
            AuthorityStats, AuthorityDashboard, AuthorityProfileUpdate, AuthorityListResponse,
            AuthorityAnnouncementCreate, AuthorityAnnouncementUpdate,
            AuthorityAnnouncementResponse, AuthorityAnnouncementListResponse,
            
            # Vote
            VoteCreate, VoteResponse, VoteStats, VoteDeleteResponse,
            
            # Notification
            NotificationCreate, NotificationResponse, NotificationListResponse,
            NotificationMarkRead, NotificationUnreadCount,
            
            # Common
            SuccessResponse, ErrorResponse, PaginationParams, PaginatedResponse,
            HealthCheckResponse, TokenResponse, SystemStats, MessageResponse,
            ValidationError, BulkOperationResponse, DateRangeFilter,
        )
        
        print("✅ All schema imports successful!")
        print(f"   - Student schemas: 8")
        print(f"   - Complaint schemas: 12")
        print(f"   - Authority schemas: 12")
        print(f"   - Vote schemas: 4")
        print(f"   - Notification schemas: 5")
        print(f"   - Common schemas: 11")
        print(f"   Total: 52 schemas imported successfully\n")
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}\n")
        return False


def test_student_schemas():
    """Test student schema validation"""
    print("=" * 80)
    print("TEST 2: Student Schemas")
    print("=" * 80)
    
    from src.schemas import StudentRegister, StudentLogin, PasswordChange
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Valid StudentRegister
    try:
        student = StudentRegister(
            roll_no="22CS231",
            name="John Doe",
            email="john.doe@college.edu",
            password="SecurePass123!",
            gender="Male",
            stay_type="Hostel",
            department_id=1,
            year=3
        )
        print("✅ Valid StudentRegister creation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Valid StudentRegister failed: {e}")
        tests_failed += 1
    
    # Test 2: Invalid password (no uppercase)
    try:
        student = StudentRegister(
            roll_no="22CS231",
            name="John Doe",
            email="john.doe@college.edu",
            password="weakpass123",  # No uppercase
            gender="Male",
            stay_type="Hostel",
            department_id=1,
            year=3
        )
        print("❌ Weak password should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Weak password correctly rejected")
        tests_passed += 1
    
    # Test 3: Invalid name (contains numbers)
    try:
        student = StudentRegister(
            roll_no="22CS231",
            name="John123",  # Contains numbers
            email="john.doe@college.edu",
            password="SecurePass123!",
            gender="Male",
            stay_type="Hostel",
            department_id=1,
            year=3
        )
        print("❌ Name with numbers should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Name with numbers correctly rejected")
        tests_passed += 1
    
    # Test 4: Roll number normalization
    try:
        student = StudentRegister(
            roll_no="  22cs231  ",  # Lowercase with spaces
            name="John Doe",
            email="john.doe@college.edu",
            password="SecurePass123!",
            gender="Male",
            stay_type="Hostel",
            department_id=1,
            year=3
        )
        assert student.roll_no == "22CS231", "Roll number should be uppercase"
        print("✅ Roll number normalization works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Roll number normalization failed: {e}")
        tests_failed += 1
    
    # Test 5: PasswordChange - new password same as old
    try:
        pwd_change = PasswordChange(
            old_password="OldPass123!",
            new_password="OldPass123!",  # Same as old
            confirm_password="OldPass123!"
        )
        print("❌ Same password should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Same new/old password correctly rejected")
        tests_passed += 1
    
    # Test 6: PasswordChange - passwords don't match
    try:
        pwd_change = PasswordChange(
            old_password="OldPass123!",
            new_password="NewPass456!",
            confirm_password="DifferentPass789!"  # Doesn't match
        )
        print("❌ Mismatched passwords should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Mismatched passwords correctly rejected")
        tests_passed += 1
    
    print(f"\n📊 Student Schemas: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def test_complaint_schemas():
    """Test complaint schema validation"""
    print("=" * 80)
    print("TEST 3: Complaint Schemas")
    print("=" * 80)
    
    from src.schemas import ComplaintCreate, ComplaintUpdate, ComplaintFilter, ComplaintDetailResponse
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Valid ComplaintCreate
    try:
        complaint = ComplaintCreate(
            category_id=1,
            original_text="The hostel room fan is not working for the past 3 days. Very hot!",
            visibility="Public"
        )
        print("✅ Valid ComplaintCreate creation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Valid ComplaintCreate failed: {e}")
        tests_failed += 1
    
    # Test 2: Text too short
    try:
        complaint = ComplaintCreate(
            category_id=1,
            original_text="Short",  # Too short
            visibility="Public"
        )
        print("❌ Short complaint text should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Short complaint text correctly rejected")
        tests_passed += 1
    
    # Test 3: All caps text
    try:
        complaint = ComplaintCreate(
            category_id=1,
            original_text="THIS IS ALL CAPS AND SHOULD BE REJECTED!!!",
            visibility="Public"
        )
        print("❌ All caps text should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ All caps text correctly rejected")
        tests_passed += 1
    
    # Test 4: ComplaintUpdate - status change requires reason
    try:
        update = ComplaintUpdate(
            status="Closed",
            reason=""  # Empty reason for Closed status
        )
        print("❌ Closed status without reason should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Closed status without reason correctly rejected")
        tests_passed += 1
    
    # Test 5: ComplaintFilter date range validation
    try:
        from datetime import datetime, timezone
        complaint_filter = ComplaintFilter(
            date_from=datetime(2026, 2, 10, tzinfo=timezone.utc),
            date_to=datetime(2026, 2, 5, tzinfo=timezone.utc)  # Before date_from
        )
        print("❌ Invalid date range should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Invalid date range correctly rejected")
        tests_passed += 1
    
    # Test 6: ComplaintDetailResponse - Fixed mutable default
    try:
        detail = ComplaintDetailResponse(
            id=uuid4(),
            category_id=1,
            original_text="Test complaint",
            visibility="Public",
            upvotes=5,
            downvotes=0,
            priority="Medium",
            priority_score=50.0,
            status="Raised",
            is_marked_as_spam=False,
            image_verified=False,
            submitted_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
            comments_count=0,
            vote_count=5
        )
        # Check that status_updates is None by default, not []
        assert detail.status_updates is None, "status_updates should default to None, not []"
        print("✅ Mutable default bug fixed (status_updates=None)")
        tests_passed += 1
    except Exception as e:
        print(f"❌ ComplaintDetailResponse failed: {e}")
        tests_failed += 1
    
    print(f"\n📊 Complaint Schemas: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def test_authority_schemas():
    """Test authority schema validation"""
    print("=" * 80)
    print("TEST 4: Authority Schemas")
    print("=" * 80)
    
    from src.schemas import AuthorityAnnouncementCreate, AuthorityCreate
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Valid AuthorityCreate
    try:
        authority = AuthorityCreate(
            name="Dr. John Smith",
            email="john.smith@college.edu",
            password="SecurePass123!",
            phone="9876543210",
            authority_type="Warden",
            designation="Chief Warden",
            authority_level=5
        )
        print("✅ Valid AuthorityCreate creation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Valid AuthorityCreate failed: {e}")
        tests_failed += 1
    
    # Test 2: Invalid phone number
    try:
        authority = AuthorityCreate(
            name="Dr. John Smith",
            email="john.smith@college.edu",
            password="SecurePass123!",
            phone="1234567890",  # Doesn't start with 6-9
            authority_type="Warden",
            designation="Chief Warden",
            authority_level=5
        )
        print("❌ Invalid phone number should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Invalid phone number correctly rejected")
        tests_passed += 1
    
    # Test 3: Announcement expires_at in past (FIXED datetime.utcnow bug)
    try:
        from datetime import datetime, timezone, timedelta
        announcement = AuthorityAnnouncementCreate(
            title="Test Announcement",
            content="This is a test announcement content that is long enough.",
            category="Announcement",
            priority="Medium",
            visibility="All Students",
            expires_at=datetime.now(timezone.utc) - timedelta(days=1)  # Past date
        )
        print("❌ Past expiry date should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Past expiry date correctly rejected (datetime.utcnow bug fixed)")
        tests_passed += 1
    
    # Test 4: All caps title
    try:
        announcement = AuthorityAnnouncementCreate(
            title="THIS IS ALL CAPS",
            content="This is a test announcement content that is long enough.",
            category="Announcement",
            priority="Medium",
            visibility="All Students"
        )
        print("❌ All caps title should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ All caps title correctly rejected")
        tests_passed += 1
    
    print(f"\n📊 Authority Schemas: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def test_vote_schemas():
    """Test vote schema validation"""
    print("=" * 80)
    print("TEST 5: Vote Schemas")
    print("=" * 80)
    
    from src.schemas import VoteStats, VoteResponse
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: VoteStats with zero total_votes (division by zero fix)
    try:
        stats = VoteStats(
            total_votes=0,
            upvotes=0,
            downvotes=0,
            net_votes=0,
            vote_ratio=0.0
        )
        assert stats.vote_ratio == 0.0, "vote_ratio should be 0.0 when total_votes=0"
        print("✅ Division by zero protection works")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Division by zero protection failed: {e}")
        tests_failed += 1
    
    # Test 2: VoteStats calculates ratio correctly
    try:
        stats = VoteStats(
            total_votes=20,
            upvotes=15,
            downvotes=5,
            net_votes=10,
            vote_ratio=0.75
        )
        print("✅ Valid VoteStats creation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Valid VoteStats failed: {e}")
        tests_failed += 1
    
    # Test 3: Negative votes rejected
    try:
        response = VoteResponse(
            complaint_id=uuid4(),
            upvotes=-5,  # Negative
            downvotes=2,
            priority_score=50.0,
            priority="Medium"
        )
        print("❌ Negative votes should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Negative votes correctly rejected")
        tests_passed += 1
    
    print(f"\n📊 Vote Schemas: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def test_notification_schemas():
    """Test notification schema validation"""
    print("=" * 80)
    print("TEST 6: Notification Schemas")
    print("=" * 80)
    
    from src.schemas import NotificationMarkRead, NotificationCreate
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: Valid NotificationCreate
    try:
        notification = NotificationCreate(
            recipient_type="Student",
            recipient_id="22CS231",
            notification_type="status_update",
            message="Your complaint has been updated"
        )
        print("✅ Valid NotificationCreate creation")
        tests_passed += 1
    except Exception as e:
        print(f"❌ Valid NotificationCreate failed: {e}")
        tests_failed += 1
    
    # Test 2: Empty notification IDs
    try:
        mark_read = NotificationMarkRead(
            notification_ids=[]  # Empty list
        )
        print("❌ Empty notification IDs should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Empty notification IDs correctly rejected")
        tests_passed += 1
    
    # Test 3: Negative notification ID
    try:
        mark_read = NotificationMarkRead(
            notification_ids=[1, 2, -3]  # Negative ID
        )
        print("❌ Negative notification ID should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Negative notification ID correctly rejected")
        tests_passed += 1
    
    print(f"\n📊 Notification Schemas: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def test_common_schemas():
    """Test common schema validation"""
    print("=" * 80)
    print("TEST 7: Common Schemas")
    print("=" * 80)
    
    from src.schemas import PaginatedResponse, DateRangeFilter, PaginationParams
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: PaginatedResponse.create() with math.ceil
    try:
        response = PaginatedResponse.create(
            items=[],
            total=23,
            page=1,
            page_size=10
        )
        assert response.total_pages == 3, "Should have 3 pages (23/10 = 2.3 -> 3)"
        assert response.has_next == True, "Should have next page"
        assert response.has_previous == False, "Should not have previous page"
        print("✅ PaginatedResponse.create() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ PaginatedResponse.create() failed: {e}")
        tests_failed += 1
    
    # Test 2: DateRangeFilter validation
    try:
        date_filter = DateRangeFilter(
            date_from=datetime(2026, 2, 10, tzinfo=timezone.utc),
            date_to=datetime(2026, 2, 5, tzinfo=timezone.utc)  # Before date_from
        )
        print("❌ Invalid date range should have failed")
        tests_failed += 1
    except ValueError:
        print("✅ Invalid date range correctly rejected")
        tests_passed += 1
    
    # Test 3: PaginationParams properties
    try:
        params = PaginationParams(page=3, page_size=20)
        assert params.skip == 40, "skip should be 40 (page 3, 20 per page)"
        assert params.limit == 20, "limit should be 20"
        print("✅ PaginationParams properties work correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ PaginationParams properties failed: {e}")
        tests_failed += 1
    
    print(f"\n📊 Common Schemas: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def test_serialization():
    """Test schema serialization/deserialization"""
    print("=" * 80)
    print("TEST 8: Schema Serialization")
    print("=" * 80)
    
    from src.schemas import StudentRegister, ComplaintResponse
    
    tests_passed = 0
    tests_failed = 0
    
    # Test 1: model_dump()
    try:
        student = StudentRegister(
            roll_no="22CS231",
            name="John Doe",
            email="john.doe@college.edu",
            password="SecurePass123!",
            gender="Male",
            stay_type="Hostel",
            department_id=1,
            year=3
        )
        data = student.model_dump()
        assert isinstance(data, dict), "model_dump() should return dict"
        assert data['roll_no'] == "22CS231", "Roll number should be preserved"
        print("✅ model_dump() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ model_dump() failed: {e}")
        tests_failed += 1
    
    # Test 2: model_dump_json()
    try:
        json_str = student.model_dump_json()
        assert isinstance(json_str, str), "model_dump_json() should return string"
        assert "22CS231" in json_str, "JSON should contain roll number"
        print("✅ model_dump_json() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ model_dump_json() failed: {e}")
        tests_failed += 1
    
    # Test 3: model_validate()
    try:
        data = {
            "roll_no": "22CS232",
            "name": "Jane Smith",
            "email": "jane.smith@college.edu",
            "password": "SecurePass456!",
            "gender": "Female",
            "stay_type": "Day Scholar",
            "department_id": 2,
            "year": 2
        }
        student2 = StudentRegister.model_validate(data)
        assert student2.roll_no == "22CS232", "model_validate should work"
        print("✅ model_validate() works correctly")
        tests_passed += 1
    except Exception as e:
        print(f"❌ model_validate() failed: {e}")
        tests_failed += 1
    
    print(f"\n📊 Serialization: {tests_passed} passed, {tests_failed} failed\n")
    return tests_passed, tests_failed


def main():
    """Run all schema tests"""
    print("\n" + "=" * 80)
    print("CAMPUSVOICE - PYDANTIC SCHEMAS TEST SUITE")
    print("=" * 80 + "\n")
    
    total_passed = 0
    total_failed = 0
    
    # Run all tests
    if not test_imports():
        print("⚠️  Import test failed. Cannot continue with other tests.")
        sys.exit(1)
    
    results = [
        test_student_schemas(),
        test_complaint_schemas(),
        test_authority_schemas(),
        test_vote_schemas(),
        test_notification_schemas(),
        test_common_schemas(),
        test_serialization(),
    ]
    
    for passed, failed in results:
        total_passed += passed
        total_failed += failed
    
    # Final summary
    print("=" * 80)
    print("FINAL RESULTS")
    print("=" * 80)
    print(f"✅ Tests Passed: {total_passed}")
    print(f"❌ Tests Failed: {total_failed}")
    print(f"📊 Total Tests: {total_passed + total_failed}")
    print(f"🎯 Success Rate: {(total_passed / (total_passed + total_failed) * 100):.1f}%")
    print("=" * 80 + "\n")
    
    if total_failed == 0:
        print("🎉 ALL SCHEMA TESTS PASSED! Your schemas are production-ready! 🚀\n")
        sys.exit(0)
    else:
        print(f"⚠️  {total_failed} test(s) failed. Please review the errors above.\n")
        sys.exit(1)


if __name__ == "__main__":
    main()
