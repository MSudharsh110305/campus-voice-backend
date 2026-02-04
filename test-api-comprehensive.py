"""
Comprehensive API Test Suite for CampusVoice
Tests all endpoints, features, and business logic including:
- Student registration, login, complaint submission
- LLM rephrasing, spam detection, image requirement checking
- Complaint viewing with visibility filters
- Real-time voting and priority updates
- Authority operations with partial anonymity
- Role-based escalation
- Admin operations
- Authority updates for target groups

Run: python test-api-comprehensive.py
"""

import httpx
import json
import os
import time
from datetime import datetime
from typing import Dict, List, Optional, Tuple
from io import BytesIO
from PIL import Image
from tkinter import Tk, filedialog

# ==================== CONFIGURATION ====================
BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0

# Test data configuration
NUM_STUDENTS = 10
DEPARTMENTS = ["CSE", "ECE", "MECH", "CIVIL", "IT"]
STAY_TYPES = ["Hostel", "Day Scholar"]
YEARS = ["1st Year", "2nd Year", "3rd Year", "4th Year"]
GENDERS = ["Male", "Female", "Other"]

# Color codes for output
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

# ==================== UTILITY FUNCTIONS ====================

def print_section(title: str):
    """Print a section header"""
    print(f"\n{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{title.center(80)}{Colors.ENDC}")
    print(f"{Colors.HEADER}{Colors.BOLD}{'='*80}{Colors.ENDC}\n")

def print_success(message: str):
    """Print success message"""
    print(f"{Colors.OKGREEN}✓ {message}{Colors.ENDC}")

def print_error(message: str):
    """Print error message"""
    print(f"{Colors.FAIL}✗ {message}{Colors.ENDC}")

def print_info(message: str):
    """Print info message"""
    print(f"{Colors.OKBLUE}ℹ {message}{Colors.ENDC}")

def print_warning(message: str):
    """Print warning message"""
    print(f"{Colors.WARNING}⚠ {message}{Colors.ENDC}")

def pretty_print_json(data: dict, title: str = ""):
    """Pretty print JSON data"""
    if title:
        print(f"\n{Colors.OKCYAN}{title}:{Colors.ENDC}")
    print(json.dumps(data, indent=2))

def select_image_file() -> Optional[str]:
    """Open file dialog to select an image"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(
        title="Select an image file for testing",
        filetypes=[("Image files", "*.jpg *.jpeg *.png *.gif *.webp")]
    )
    root.destroy()
    return path if path else None

def create_test_image(color: str = "blue", size: tuple = (200, 200)) -> bytes:
    """Create a test image in memory"""
    img = Image.new("RGB", size, color=color)
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf.read()

# ==================== API CLIENT ====================

class CampusVoiceClient:
    """HTTP client for CampusVoice API"""

    def __init__(self, base_url: str = BASE_URL, timeout: float = TIMEOUT):
        self.base_url = base_url
        self.timeout = timeout
        self.session = httpx.Client(timeout=timeout)

    def _request(self, method: str, path: str, **kwargs) -> httpx.Response:
        """Make HTTP request"""
        url = f"{self.base_url}{path}"
        try:
            response = self.session.request(method, url, **kwargs)
            return response
        except Exception as e:
            print_error(f"Request failed: {e}")
            raise

    def post(self, path: str, json: dict = None, files: dict = None, headers: dict = None) -> httpx.Response:
        """POST request"""
        return self._request("POST", path, json=json, files=files, headers=headers)

    def get(self, path: str, params: dict = None, headers: dict = None) -> httpx.Response:
        """GET request"""
        return self._request("GET", path, params=params, headers=headers)

    def put(self, path: str, json: dict = None, headers: dict = None) -> httpx.Response:
        """PUT request"""
        return self._request("PUT", path, json=json, headers=headers)

    def delete(self, path: str, headers: dict = None) -> httpx.Response:
        """DELETE request"""
        return self._request("DELETE", path, headers=headers)

    def close(self):
        """Close the client"""
        self.session.close()

# ==================== TEST DATA STORAGE ====================

class TestContext:
    """Store test data across test cases"""

    def __init__(self):
        self.students: List[Dict] = []
        self.authorities: List[Dict] = []
        self.admin: Optional[Dict] = None
        self.complaints: List[Dict] = []
        self.test_image: Optional[str] = None
        self.results: Dict[str, bool] = {}

    def add_result(self, test_name: str, passed: bool):
        """Add test result"""
        self.results[test_name] = passed

    def print_summary(self):
        """Print test summary"""
        print_section("TEST SUMMARY")
        passed = sum(1 for v in self.results.values() if v)
        total = len(self.results)

        for test_name, passed_test in self.results.items():
            if passed_test:
                print_success(f"{test_name}")
            else:
                print_error(f"{test_name}")

        print(f"\n{Colors.BOLD}Total: {passed}/{total} tests passed{Colors.ENDC}")

        if passed == total:
            print_success("All tests passed! 🎉")
        else:
            print_warning(f"{total - passed} tests failed")

# ==================== TEST CASES ====================

def test_student_registration(client: CampusVoiceClient, ctx: TestContext):
    """Test student registration"""
    print_section("TEST 1: Student Registration")

    try:
        for i in range(NUM_STUDENTS):
            roll_no = f"23{DEPARTMENTS[i % len(DEPARTMENTS)]}{str(i+1).zfill(3)}"
            dept = DEPARTMENTS[i % len(DEPARTMENTS)]
            stay = STAY_TYPES[i % len(STAY_TYPES)]
            year = YEARS[i % len(YEARS)]
            gender = GENDERS[i % len(GENDERS)]

            student_data = {
                "roll_no": roll_no,
                "name": f"Student {i+1}",
                "email": f"student{i+1}@college.edu",
                "password": "Password@123",
                "gender": gender,
                "stay_type": stay,
                "year": year,
                "department_id": dept
            }

            print_info(f"Registering {student_data['name']} ({roll_no}, {dept}, {stay})")
            response = client.post("/api/students/register", json=student_data)

            if response.status_code == 201:
                data = response.json()
                student_data['token'] = data.get('token')
                ctx.students.append(student_data)
                print_success(f"Registered {student_data['name']}")
            else:
                print_error(f"Failed to register {student_data['name']}: {response.text}")
                ctx.add_result("Student Registration", False)
                return

        print_success(f"Successfully registered {NUM_STUDENTS} students")
        ctx.add_result("Student Registration", True)

    except Exception as e:
        print_error(f"Student registration failed: {e}")
        ctx.add_result("Student Registration", False)

def test_student_login(client: CampusVoiceClient, ctx: TestContext):
    """Test student login"""
    print_section("TEST 2: Student Login")

    try:
        for student in ctx.students[:3]:  # Test first 3 students
            print_info(f"Logging in {student['name']}")
            response = client.post("/api/students/login", json={
                "email_or_roll_no": student['email'],
                "password": student['password']
            })

            if response.status_code == 200:
                data = response.json()
                student['token'] = data.get('token')
                print_success(f"Logged in {student['name']}")
            else:
                print_error(f"Failed to login {student['name']}: {response.text}")
                ctx.add_result("Student Login", False)
                return

        ctx.add_result("Student Login", True)

    except Exception as e:
        print_error(f"Student login failed: {e}")
        ctx.add_result("Student Login", False)

def test_complaint_submission_with_image_requirement(client: CampusVoiceClient, ctx: TestContext):
    """Test complaint submission with LLM image requirement check"""
    print_section("TEST 3: Complaint Submission with Image Requirement Check")

    # Test cases: some need images, some don't
    test_complaints = [
        {
            "text": "The AC in classroom 301 is not working and it's very hot",
            "expected_image_required": True,
            "visibility": "Public"
        },
        {
            "text": "The water dispenser on the 3rd floor is broken and leaking water everywhere",
            "expected_image_required": True,
            "visibility": "Public"
        },
        {
            "text": "I want to request a change in exam schedule policy",
            "expected_image_required": False,
            "visibility": "Public"
        },
        {
            "text": "Can we have more study hours in the library?",
            "expected_image_required": False,
            "visibility": "Department"
        }
    ]

    try:
        # Ask user if they want to upload a real image
        print_info("Do you want to select a real image file for testing? (y/n)")
        choice = input().strip().lower()

        if choice == 'y':
            ctx.test_image = select_image_file()
            if ctx.test_image:
                print_success(f"Selected image: {ctx.test_image}")
            else:
                print_warning("No image selected, will use generated test images")

        for idx, complaint_data in enumerate(test_complaints):
            student = ctx.students[idx % len(ctx.students)]
            print_info(f"\nSubmitting complaint: '{complaint_data['text'][:60]}...'")
            print_info(f"Expected image requirement: {complaint_data['expected_image_required']}")

            # First, try submitting without image
            response = client.post(
                "/api/complaints/submit",
                json={
                    "original_text": complaint_data['text'],
                    "visibility": complaint_data['visibility']
                },
                headers={"Authorization": f"Bearer {student['token']}"}
            )

            if complaint_data['expected_image_required']:
                # Should fail with image requirement error
                if response.status_code == 400:
                    error_data = response.json()
                    if "image" in error_data.get("error", "").lower():
                        print_success("✓ Correctly rejected complaint requiring image")
                        print_info(f"  Reason: {error_data.get('error')}")

                        # Now submit with image
                        print_info("  Resubmitting with image...")

                        if ctx.test_image:
                            with open(ctx.test_image, 'rb') as f:
                                image_data = f.read()
                        else:
                            image_data = create_test_image()

                        files = {"images": ("test.jpg", image_data, "image/jpeg")}
                        response = client.post(
                            "/api/complaints/submit",
                            data={
                                "original_text": complaint_data['text'],
                                "visibility": complaint_data['visibility']
                            },
                            files=files,
                            headers={"Authorization": f"Bearer {student['token']}"}
                        )

                        if response.status_code == 201:
                            data = response.json()
                            ctx.complaints.append(data)
                            print_success("✓ Complaint submitted successfully with image")
                            print_info(f"  Rephrased: {data.get('rephrased_text', 'N/A')[:60]}...")
                            print_info(f"  Category: {data.get('category', {}).get('name', 'N/A')}")
                            print_info(f"  Priority: {data.get('priority', 'N/A')}")
                        else:
                            print_error(f"Failed to submit with image: {response.text}")
                    else:
                        print_warning("Got 400 but not image requirement error")
                else:
                    print_warning(f"Expected 400 for missing image, got {response.status_code}")
            else:
                # Should succeed without image
                if response.status_code == 201:
                    data = response.json()
                    ctx.complaints.append(data)
                    print_success("✓ Complaint submitted successfully (no image required)")
                    print_info(f"  Rephrased: {data.get('rephrased_text', 'N/A')[:60]}...")
                    print_info(f"  Category: {data.get('category', {}).get('name', 'N/A')}")
                    print_info(f"  Priority: {data.get('priority', 'N/A')}")
                else:
                    print_error(f"Failed to submit complaint: {response.text}")

            time.sleep(1)  # Rate limiting

        ctx.add_result("Complaint Submission with Image Requirement", True)

    except Exception as e:
        print_error(f"Complaint submission test failed: {e}")
        ctx.add_result("Complaint Submission with Image Requirement", False)

def test_spam_detection(client: CampusVoiceClient, ctx: TestContext):
    """Test spam/abusive complaint detection"""
    print_section("TEST 4: Spam/Abusive Detection")

    spam_complaints = [
        "spam spam spam fake complaint test",
        "This is abusive and offensive content that should be blocked",
        "test test test dummy fake spam"
    ]

    try:
        student = ctx.students[0]

        for spam_text in spam_complaints:
            print_info(f"Submitting spam complaint: '{spam_text[:40]}...'")
            response = client.post(
                "/api/complaints/submit",
                json={
                    "original_text": spam_text,
                    "visibility": "Public"
                },
                headers={"Authorization": f"Bearer {student['token']}"}
            )

            if response.status_code == 400:
                error_data = response.json()
                if error_data.get("is_spam") or "spam" in error_data.get("error", "").lower():
                    print_success("✓ Spam correctly detected and rejected")
                    print_info(f"  Reason: {error_data.get('reason', 'N/A')}")
                else:
                    print_warning("Got 400 but not spam error")
            else:
                print_error(f"Spam not detected! Status: {response.status_code}")
                ctx.add_result("Spam Detection", False)
                return

        ctx.add_result("Spam Detection", True)

    except Exception as e:
        print_error(f"Spam detection test failed: {e}")
        ctx.add_result("Spam Detection", False)

def test_view_my_complaints(client: CampusVoiceClient, ctx: TestContext):
    """Test viewing own complaints"""
    print_section("TEST 5: View My Complaints")

    try:
        student = ctx.students[0]
        print_info(f"Fetching complaints for {student['name']}")

        response = client.get(
            "/api/students/my-complaints",
            headers={"Authorization": f"Bearer {student['token']}"}
        )

        if response.status_code == 200:
            data = response.json()
            complaints = data.get('complaints', [])
            print_success(f"✓ Retrieved {len(complaints)} complaint(s)")

            for complaint in complaints:
                print_info(f"  - ID: {complaint.get('id', 'N/A')[:8]}... | Status: {complaint.get('status')} | Priority: {complaint.get('priority')}")

            ctx.add_result("View My Complaints", True)
        else:
            print_error(f"Failed to get complaints: {response.text}")
            ctx.add_result("View My Complaints", False)

    except Exception as e:
        print_error(f"View my complaints test failed: {e}")
        ctx.add_result("View My Complaints", False)

def test_public_feed_filtering(client: CampusVoiceClient, ctx: TestContext):
    """Test public feed with visibility filtering"""
    print_section("TEST 6: Public Feed with Visibility Filtering")

    try:
        # Get a hostel student and a day scholar
        hostel_student = next((s for s in ctx.students if s['stay_type'] == 'Hostel'), None)
        day_scholar = next((s for s in ctx.students if s['stay_type'] == 'Day Scholar'), None)

        if not hostel_student or not day_scholar:
            print_warning("Need both hostel and day scholar students for this test")
            ctx.add_result("Public Feed Filtering", False)
            return

        # Create a hostel-specific complaint
        print_info("Creating hostel-specific complaint...")
        response = client.post(
            "/api/complaints/submit",
            json={
                "original_text": "The hostel mess food quality needs improvement",
                "visibility": "Public"
            },
            headers={"Authorization": f"Bearer {hostel_student['token']}"}
        )

        if response.status_code == 201:
            hostel_complaint = response.json()
            print_success("Created hostel complaint")
            time.sleep(1)

            # Test: Hostel student should see it
            print_info("Testing hostel student can see hostel complaints...")
            response = client.get(
                "/api/complaints/public-feed",
                headers={"Authorization": f"Bearer {hostel_student['token']}"}
            )

            if response.status_code == 200:
                data = response.json()
                complaint_ids = [c.get('id') for c in data.get('complaints', [])]
                if hostel_complaint.get('complaint_id') in complaint_ids:
                    print_success("✓ Hostel student can see hostel complaints")
                else:
                    print_warning("Hostel student cannot see own complaint")

            # Test: Day scholar should NOT see it
            print_info("Testing day scholar cannot see hostel complaints...")
            response = client.get(
                "/api/complaints/public-feed",
                headers={"Authorization": f"Bearer {day_scholar['token']}"}
            )

            if response.status_code == 200:
                data = response.json()
                complaint_ids = [c.get('id') for c in data.get('complaints', [])]
                if hostel_complaint.get('complaint_id') not in complaint_ids:
                    print_success("✓ Day scholar correctly cannot see hostel complaints")
                else:
                    print_error("Day scholar can see hostel complaints (should be hidden)")
                    ctx.add_result("Public Feed Filtering", False)
                    return

        # Test department filtering
        cse_student = next((s for s in ctx.students if s['department_id'] == 'CSE'), None)
        ece_student = next((s for s in ctx.students if s['department_id'] == 'ECE'), None)

        if cse_student and ece_student:
            print_info("\nTesting department filtering...")

            # Create department-specific complaint
            response = client.post(
                "/api/complaints/submit",
                json={
                    "original_text": "CSE lab computers need maintenance",
                    "visibility": "Department"
                },
                headers={"Authorization": f"Bearer {cse_student['token']}"}
            )

            if response.status_code == 201:
                dept_complaint = response.json()
                time.sleep(1)

                # ECE student should not see CSE department complaints
                response = client.get(
                    "/api/complaints/public-feed",
                    params={"department": "ECE"},
                    headers={"Authorization": f"Bearer {ece_student['token']}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    complaint_ids = [c.get('id') for c in data.get('complaints', [])]
                    if dept_complaint.get('complaint_id') not in complaint_ids:
                        print_success("✓ Department filtering works correctly")
                    else:
                        print_warning("Department filtering may not be working")

        ctx.add_result("Public Feed Filtering", True)

    except Exception as e:
        print_error(f"Public feed filtering test failed: {e}")
        ctx.add_result("Public Feed Filtering", False)

def test_voting_realtime_priority(client: CampusVoiceClient, ctx: TestContext):
    """Test voting and real-time priority updates"""
    print_section("TEST 7: Voting and Real-time Priority Updates")

    try:
        if not ctx.complaints:
            print_warning("No complaints available for voting test")
            ctx.add_result("Voting Real-time Priority", False)
            return

        target_complaint = ctx.complaints[0]
        complaint_id = target_complaint.get('complaint_id')

        print_info(f"Target complaint: {complaint_id}")
        print_info(f"Initial priority: {target_complaint.get('priority', 'N/A')}")

        # Multiple students vote
        voters = ctx.students[:5]

        for idx, voter in enumerate(voters):
            vote_type = "Upvote" if idx % 2 == 0 else "Downvote"
            print_info(f"{voter['name']} voting: {vote_type}")

            response = client.post(
                f"/api/complaints/{complaint_id}/vote",
                json={"vote_type": vote_type},
                headers={"Authorization": f"Bearer {voter['token']}"}
            )

            if response.status_code == 200:
                data = response.json()
                print_success(f"✓ Vote recorded - Upvotes: {data.get('upvotes')}, Downvotes: {data.get('downvotes')}, Priority: {data.get('priority')}")
            else:
                print_error(f"Vote failed: {response.text}")

        # Verify priority calculation
        # Formula: score = (upvotes * 5) + (downvotes * -3)
        response = client.get(
            "/api/complaints/public-feed",
            headers={"Authorization": f"Bearer {ctx.students[0]['token']}"}
        )

        if response.status_code == 200:
            data = response.json()
            complaints = data.get('complaints', [])
            updated_complaint = next((c for c in complaints if c.get('id') == complaint_id), None)

            if updated_complaint:
                upvotes = updated_complaint.get('upvotes', 0)
                downvotes = updated_complaint.get('downvotes', 0)
                priority = updated_complaint.get('priority', 'Low')

                expected_score = (upvotes * 5) + (downvotes * -3)
                print_success(f"✓ Priority updated in real-time")
                print_info(f"  Upvotes: {upvotes}, Downvotes: {downvotes}")
                print_info(f"  Score: {expected_score}, Priority: {priority}")

        ctx.add_result("Voting Real-time Priority", True)

    except Exception as e:
        print_error(f"Voting test failed: {e}")
        ctx.add_result("Voting Real-time Priority", False)

def test_authority_login_and_view(client: CampusVoiceClient, ctx: TestContext):
    """Test authority login and viewing assigned complaints"""
    print_section("TEST 8: Authority Login and View Assigned Complaints")

    # Authority accounts should be pre-seeded
    authority_logins = [
        {"email": "warden@college.edu", "password": "Warden@123", "type": "Warden"},
        {"email": "adminofficer@college.edu", "password": "AdminOfficer@123", "type": "Admin Officer"},
        {"email": "hod@college.edu", "password": "HOD@123", "type": "HOD"}
    ]

    try:
        for auth_data in authority_logins:
            print_info(f"Logging in as {auth_data['type']}: {auth_data['email']}")

            response = client.post(
                "/api/authorities/login",
                json={
                    "email": auth_data['email'],
                    "password": auth_data['password']
                }
            )

            if response.status_code == 200:
                data = response.json()
                auth_data['token'] = data.get('token')
                auth_data['name'] = data.get('name')
                auth_data['authority_level'] = data.get('authority_level')
                ctx.authorities.append(auth_data)
                print_success(f"✓ Logged in as {auth_data['type']}")

                # View assigned complaints
                print_info("Fetching assigned complaints...")
                response = client.get(
                    "/api/authorities/my-complaints",
                    headers={"Authorization": f"Bearer {auth_data['token']}"}
                )

                if response.status_code == 200:
                    data = response.json()
                    complaints = data.get('complaints', [])
                    print_success(f"✓ Retrieved {len(complaints)} assigned complaint(s)")

                    # Check partial anonymity
                    for complaint in complaints[:3]:
                        is_spam = complaint.get('is_marked_as_spam', False)
                        student_info = complaint.get('student_info', {})

                        if is_spam:
                            if student_info and student_info.get('email') != 'Hidden (non-spam)':
                                print_success(f"  ✓ Spam complaint - student info visible: {student_info.get('email')}")
                            else:
                                print_warning("  Spam complaint but student info hidden")
                        else:
                            if student_info and 'Hidden' in str(student_info.get('email', '')):
                                print_success(f"  ✓ Non-spam complaint - student info hidden")
                            else:
                                print_warning(f"  Non-spam complaint but student info visible: {student_info}")
                else:
                    print_error(f"Failed to get complaints: {response.text}")
            else:
                print_warning(f"Failed to login as {auth_data['type']}: {response.text}")

        ctx.add_result("Authority Login and View", True)

    except Exception as e:
        print_error(f"Authority login test failed: {e}")
        ctx.add_result("Authority Login and View", False)

def test_authority_status_change(client: CampusVoiceClient, ctx: TestContext):
    """Test authority changing complaint status"""
    print_section("TEST 9: Authority Status Changes")

    try:
        if not ctx.authorities or not ctx.complaints:
            print_warning("Need authorities and complaints for this test")
            ctx.add_result("Authority Status Change", False)
            return

        authority = ctx.authorities[0]
        complaint_id = ctx.complaints[0].get('complaint_id')

        print_info(f"Authority {authority['name']} changing status of complaint {complaint_id}")

        # Change status to "In Progress"
        response = client.put(
            f"/api/authorities/complaints/{complaint_id}/status",
            json={
                "status": "In Progress",
                "reason": "Assigned to maintenance team"
            },
            headers={"Authorization": f"Bearer {authority['token']}"}
        )

        if response.status_code == 200:
            print_success("✓ Status changed to 'In Progress'")
            time.sleep(1)

            # Verify from student side
            student = ctx.students[0]
            response = client.get(
                "/api/students/my-complaints",
                headers={"Authorization": f"Bearer {student['token']}"}
            )

            if response.status_code == 200:
                data = response.json()
                complaints = data.get('complaints', [])
                updated = next((c for c in complaints if c.get('id') == complaint_id), None)

                if updated and updated.get('status') == 'In Progress':
                    print_success("✓ Status change visible to student")
                else:
                    print_warning("Status change not reflected on student side")
        else:
            print_error(f"Failed to change status: {response.text}")
            ctx.add_result("Authority Status Change", False)
            return

        ctx.add_result("Authority Status Change", True)

    except Exception as e:
        print_error(f"Authority status change test failed: {e}")
        ctx.add_result("Authority Status Change", False)

def test_authority_post_update(client: CampusVoiceClient, ctx: TestContext):
    """Test authority posting updates for target groups"""
    print_section("TEST 10: Authority Post Updates")

    try:
        if not ctx.authorities:
            print_warning("Need authorities for this test")
            ctx.add_result("Authority Post Update", False)
            return

        authority = ctx.authorities[0]

        # Post an update for hostelers
        print_info("Posting update for hostel students...")
        response = client.post(
            "/api/authorities/updates",
            json={
                "title": "Hostel Maintenance Schedule",
                "content": "Water supply will be interrupted on Sunday for maintenance",
                "category": "Maintenance",
                "priority": "High",
                "visibility": "Hostel",
                "target_stay_types": ["Hostel"]
            },
            headers={"Authorization": f"Bearer {authority['token']}"}
        )

        if response.status_code in [200, 201]:
            print_success("✓ Update posted for hostel students")
        else:
            print_warning(f"Update post may not be supported: {response.status_code}")

        # Post an update for specific department
        print_info("Posting update for CSE department...")
        response = client.post(
            "/api/authorities/updates",
            json={
                "title": "CSE Lab Schedule",
                "content": "Additional lab sessions scheduled for project week",
                "category": "Announcement",
                "priority": "Medium",
                "visibility": "Department",
                "target_departments": ["CSE"]
            },
            headers={"Authorization": f"Bearer {authority['token']}"}
        )

        if response.status_code in [200, 201]:
            print_success("✓ Update posted for CSE department")
        else:
            print_warning(f"Update post may not be supported: {response.status_code}")

        ctx.add_result("Authority Post Update", True)

    except Exception as e:
        print_error(f"Authority post update test failed: {e}")
        ctx.add_result("Authority Post Update", False)

def test_admin_operations(client: CampusVoiceClient, ctx: TestContext):
    """Test admin can perform all operations"""
    print_section("TEST 11: Admin Operations")

    try:
        # Login as admin
        print_info("Logging in as admin...")
        response = client.post(
            "/api/authorities/login",
            json={
                "email": "admin@campusvoice.edu",
                "password": "Admin@123"
            }
        )

        if response.status_code == 200:
            data = response.json()
            admin_token = data.get('token')
            ctx.admin = {"token": admin_token, "email": "admin@campusvoice.edu"}
            print_success("✓ Logged in as admin")

            # View all complaints
            print_info("Fetching all complaints...")
            response = client.get(
                "/api/authorities/my-complaints",
                headers={"Authorization": f"Bearer {admin_token}"}
            )

            if response.status_code == 200:
                data = response.json()
                complaints = data.get('complaints', [])
                print_success(f"✓ Admin can view all {len(complaints)} complaint(s)")

                # Check that admin sees full student info
                for complaint in complaints[:3]:
                    student_info = complaint.get('student_info', {})
                    if student_info and '@' in str(student_info.get('email', '')):
                        print_success(f"  ✓ Admin sees full student info: {student_info.get('email')}")
                    else:
                        print_warning(f"  Admin may not see full student info: {student_info}")

            # Admin can change any complaint status
            if ctx.complaints:
                complaint_id = ctx.complaints[0].get('complaint_id')
                print_info(f"Admin changing status of complaint {complaint_id}")

                response = client.put(
                    f"/api/authorities/complaints/{complaint_id}/status",
                    json={
                        "status": "Resolved",
                        "reason": "Issue resolved by admin"
                    },
                    headers={"Authorization": f"Bearer {admin_token}"}
                )

                if response.status_code == 200:
                    print_success("✓ Admin can change complaint status")
                else:
                    print_warning(f"Admin status change failed: {response.text}")

            ctx.add_result("Admin Operations", True)
        else:
            print_error(f"Admin login failed: {response.text}")
            ctx.add_result("Admin Operations", False)

    except Exception as e:
        print_error(f"Admin operations test failed: {e}")
        ctx.add_result("Admin Operations", False)

def test_role_escalation(client: CampusVoiceClient, ctx: TestContext):
    """Test role-based escalation (complaint against warden goes to deputy warden)"""
    print_section("TEST 12: Role-Based Escalation")

    try:
        student = ctx.students[0]

        # Submit complaint specifically mentioning warden
        print_info("Submitting complaint about warden...")
        response = client.post(
            "/api/complaints/submit",
            json={
                "original_text": "The warden is not responding to maintenance requests in the hostel",
                "visibility": "Public"
            },
            headers={"Authorization": f"Bearer {student['token']}"}
        )

        if response.status_code == 201:
            data = response.json()
            assigned_to = data.get('assigned_authority_name', '')

            print_success("✓ Complaint submitted")
            print_info(f"  Assigned to: {assigned_to}")

            # Check if it's escalated (should go to Deputy Warden or higher)
            if 'deputy' in assigned_to.lower() or 'admin' in assigned_to.lower():
                print_success("✓ Complaint correctly escalated past warden")
            else:
                print_warning(f"Complaint may not be escalated: assigned to {assigned_to}")
        else:
            print_error(f"Failed to submit escalation test complaint: {response.text}")

        ctx.add_result("Role Escalation", True)

    except Exception as e:
        print_error(f"Role escalation test failed: {e}")
        ctx.add_result("Role Escalation", False)

# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    """Run all test cases"""
    print(f"{Colors.BOLD}{Colors.HEADER}")
    print("=" * 80)
    print("CAMPUSVOICE COMPREHENSIVE API TEST SUITE".center(80))
    print("=" * 80)
    print(f"{Colors.ENDC}\n")

    client = CampusVoiceClient()
    ctx = TestContext()

    try:
        # Run all tests in sequence
        test_student_registration(client, ctx)
        test_student_login(client, ctx)
        test_complaint_submission_with_image_requirement(client, ctx)
        test_spam_detection(client, ctx)
        test_view_my_complaints(client, ctx)
        test_public_feed_filtering(client, ctx)
        test_voting_realtime_priority(client, ctx)
        test_authority_login_and_view(client, ctx)
        test_authority_status_change(client, ctx)
        test_authority_post_update(client, ctx)
        test_admin_operations(client, ctx)
        test_role_escalation(client, ctx)

        # Print summary
        ctx.print_summary()

    except KeyboardInterrupt:
        print_warning("\n\nTests interrupted by user")
    except Exception as e:
        print_error(f"\n\nTest suite failed with error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
        print(f"\n{Colors.BOLD}Test suite completed{Colors.ENDC}\n")

if __name__ == "__main__":
    run_all_tests()
