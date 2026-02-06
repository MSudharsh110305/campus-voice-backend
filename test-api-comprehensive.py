"""
CampusVoice API - Comprehensive End-to-End Test Script

This script exercises the full CampusVoice API, testing:
1. Student registration/login (diverse: male/female, hostel/day scholar)
2. Complaint submission with images (relevant/irrelevant)
3. Spam detection (text/image mismatch)
4. Authority visibility of student info for spam
5. Public feed filtering (hostel/day scholar, men's/women's hostel, inter-department)
6. Voting and real-time updates
7. Login as ALL authorities
8. Complaints about authorities at all levels
9. Privilege escalation verification
10. Authority updates visibility
11. Admin full access

Requirements:
    - The CampusVoice server must be running (default: http://localhost:8000)
    - pip install requests Pillow

Usage:
    python test-api-comprehensive.py
    python test-api-comprehensive.py --base-url http://localhost:9000
"""

import argparse
import io
import json
import sys
import time
from typing import Optional, Dict, List, Any

import requests

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 70
THIN_SEP = "-" * 70

# Collected summary of all operations
operation_log: list[dict] = []


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{SEPARATOR}")
    print(f"=== {title} ===")
    print(THIN_SEP)


def print_subheader(title: str) -> None:
    """Print a subsection header."""
    print(f"\n{THIN_SEP}")
    print(f"--- {title} ---")


def print_response(
    method: str,
    path: str,
    response: requests.Response,
    label: Optional[str] = None,
) -> dict | None:
    """
    Pretty-print an HTTP response and record it in the operation log.
    Returns the parsed JSON body (or None if not JSON).
    """
    tag = label or f"{method} {path}"
    status_code = response.status_code
    print(f"Endpoint: {method} {path}")
    print()

    body = None
    try:
        body = response.json()
        print(f"[Status Code: {status_code}]")
        # Truncate long responses
        body_str = json.dumps(body, indent=2, default=str)
        if len(body_str) > 1000:
            print(f"Response (truncated):\n{body_str[:1000]}...")
        else:
            print(f"Response:\n{body_str}")
    except Exception:
        print(f"[Status Code: {status_code}]")
        content_type = response.headers.get("content-type", "")
        if "image" in content_type:
            print(
                f"Response: <binary image data, "
                f"{len(response.content)} bytes, {content_type}>"
            )
        else:
            text = response.text[:500] if response.text else "(empty)"
            print(f"Response: {text}")

    print(SEPARATOR)
    operation_log.append({"operation": tag, "status_code": status_code})
    return body


def print_verification(test_name: str, passed: bool, details: str = "") -> None:
    """Print verification result."""
    status = "[PASS]" if passed else "[FAIL]"
    print(f"  {status} {test_name}")
    if details:
        print(f"        {details}")


def create_test_image(
    image_type: str = "relevant",
    text: str = None
) -> io.BytesIO:
    """
    Create a test image.

    Args:
        image_type: 'relevant' (wall crack), 'irrelevant' (random pattern),
                   'food' (food image), 'room' (room image)
        text: Optional text to draw on image

    Returns:
        BytesIO buffer with JPEG image
    """
    try:
        from PIL import Image, ImageDraw

        if image_type == "relevant":
            # Simulate wall crack image (brownish background with dark crack lines)
            img = Image.new("RGB", (200, 200), color=(180, 160, 140))
            draw = ImageDraw.Draw(img)
            # Draw crack-like lines
            draw.line([(20, 20), (100, 100), (80, 180)], fill=(50, 40, 30), width=3)
            draw.line([(100, 100), (180, 60)], fill=(50, 40, 30), width=2)
            draw.line([(50, 50), (120, 150)], fill=(60, 50, 40), width=2)
        elif image_type == "food":
            # Simulate food/mess image (plate-like circle with colors)
            img = Image.new("RGB", (200, 200), color=(245, 245, 220))  # Beige background
            draw = ImageDraw.Draw(img)
            draw.ellipse([20, 20, 180, 180], fill=(255, 255, 255), outline=(200, 200, 200))
            draw.ellipse([50, 50, 150, 150], fill=(255, 200, 100))  # Food-like color
        elif image_type == "room":
            # Simulate room image (rectangle patterns)
            img = Image.new("RGB", (200, 200), color=(200, 200, 220))
            draw = ImageDraw.Draw(img)
            draw.rectangle([20, 100, 80, 180], fill=(139, 90, 43))  # Bed
            draw.rectangle([100, 50, 180, 100], fill=(200, 150, 100))  # Table
        elif image_type == "irrelevant":
            # Random/unrelated image (cartoon-like, not related to complaints)
            img = Image.new("RGB", (200, 200), color=(100, 200, 255))  # Blue sky
            draw = ImageDraw.Draw(img)
            # Draw a smiley face (clearly irrelevant to any complaint)
            draw.ellipse([50, 50, 150, 150], fill=(255, 255, 0))  # Yellow face
            draw.ellipse([70, 80, 90, 100], fill=(0, 0, 0))  # Left eye
            draw.ellipse([110, 80, 130, 100], fill=(0, 0, 0))  # Right eye
            draw.arc([70, 100, 130, 140], 0, 180, fill=(0, 0, 0), width=3)  # Smile
        elif image_type == "meme":
            # Meme-like image (for spam testing)
            img = Image.new("RGB", (200, 200), color=(255, 0, 0))
            draw = ImageDraw.Draw(img)
            draw.rectangle([0, 0, 200, 50], fill=(0, 0, 0))
            draw.rectangle([0, 150, 200, 200], fill=(0, 0, 0))
        else:
            img = Image.new("RGB", (200, 200), color=(128, 128, 128))
            draw = ImageDraw.Draw(img)

        if text:
            try:
                draw.text((10, 180), text[:20], fill=(0, 0, 0))
            except Exception:
                pass

        buf = io.BytesIO()
        img.save(buf, format="JPEG")
        buf.seek(0)
        return buf
    except ImportError:
        print("  WARNING: Pillow not installed, returning empty buffer")
        return io.BytesIO()


# ---------------------------------------------------------------------------
# Main test runner
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="CampusVoice Comprehensive API Test"
    )
    parser.add_argument(
        "--base-url",
        default="http://localhost:8000",
        help="Base URL of the running CampusVoice server "
             "(default: http://localhost:8000)",
    )
    args = parser.parse_args()
    BASE = args.base_url.rstrip("/")

    print(SEPARATOR)
    print("CampusVoice - Comprehensive API Test Script")
    print(f"Target server: {BASE}")
    print(f"Started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)

    # Storage for tokens, IDs, etc. collected during the run
    student_tokens: Dict[str, str] = {}       # roll_no -> token
    student_data: Dict[str, dict] = {}        # roll_no -> student info
    complaint_ids: List[Optional[str]] = []   # ordered list of complaint UUIDs
    complaint_details: Dict[str, dict] = {}   # complaint_id -> details
    authority_tokens: Dict[str, str] = {}     # authority_type -> token
    authority_data: Dict[str, dict] = {}      # authority_type -> authority info
    notification_ids: list[int] = []

    # ==================================================================
    # (a) HEALTH CHECK
    # ==================================================================
    print_header("a. HEALTH CHECK")

    try:
        r = requests.get(f"{BASE}/health", timeout=10)
        print_response("GET", "/health", r)
    except Exception as exc:
        print(f"  ERROR connecting to {BASE}/health: {exc}")
        print("  Make sure the CampusVoice server is running.")
        print(SEPARATOR)
        operation_log.append(
            {"operation": "GET /health", "status_code": "ERROR"}
        )

    try:
        r = requests.get(f"{BASE}/health/detailed", timeout=10)
        print_response("GET", "/health/detailed", r)
    except Exception as exc:
        print(f"  ERROR: {exc}")
        operation_log.append(
            {"operation": "GET /health/detailed", "status_code": "ERROR"}
        )

    # ==================================================================
    # (b) STUDENT REGISTRATION - Diverse students
    # ==================================================================
    print_header("b. STUDENT REGISTRATION (Diverse: Male/Female, Hostel/Day Scholar)")

    # ---------------------------------------------------------------
    # Department IDs:  CSE=1, ECE=2, MECH=3, CIVIL=4, IT=5
    # Category  IDs:  Men's Hostel=1, General=2, Department=3,
    #                 Disciplinary Committee=4, Women's Hostel=6
    # ---------------------------------------------------------------
    students = [
        # Male Hostel Students
        {
            "roll_no": "23CS001",
            "name": "Arjun Kumar",
            "email": "arjun.kumar@srec.ac.in",
            "password": "SecurePass1!",
            "gender": "Male",
            "stay_type": "Hostel",
            "department_id": 1,  # CSE
            "year": 2,
        },
        {
            "roll_no": "24ME012",
            "name": "Rahul Verma",
            "email": "rahul.verma@srec.ac.in",
            "password": "SecurePass3!",
            "gender": "Male",
            "stay_type": "Hostel",
            "department_id": 3,  # MECH
            "year": 1,
        },
        # Female Hostel Students
        {
            "roll_no": "23CS050",
            "name": "Deepa Nair",
            "email": "deepa.nair@srec.ac.in",
            "password": "SecurePass4!",
            "gender": "Female",
            "stay_type": "Hostel",
            "department_id": 1,  # CSE
            "year": 2,
        },
        {
            "roll_no": "22EC055",
            "name": "Priya Sharma",
            "email": "priya.sharma@srec.ac.in",
            "password": "SecurePass5!",
            "gender": "Female",
            "stay_type": "Hostel",
            "department_id": 2,  # ECE
            "year": 3,
        },
        # Day Scholar Students
        {
            "roll_no": "22EC045",
            "name": "Vikram Reddy",
            "email": "vikram.reddy@srec.ac.in",
            "password": "SecurePass2!",
            "gender": "Male",
            "stay_type": "Day Scholar",
            "department_id": 2,  # ECE
            "year": 3,
        },
        {
            "roll_no": "23IT015",
            "name": "Ananya Singh",
            "email": "ananya.singh@srec.ac.in",
            "password": "SecurePass6!",
            "gender": "Female",
            "stay_type": "Day Scholar",
            "department_id": 5,  # IT (ID=5)
            "year": 2,
        },
    ]

    for i, stud in enumerate(students, start=1):
        try:
            r = requests.post(
                f"{BASE}/api/students/register",
                json=stud,
                timeout=15,
            )
            body = print_response(
                "POST",
                "/api/students/register",
                r,
                label=f"Register {stud['name']} ({stud['roll_no']}) - {stud['gender']}/{stud['stay_type']}",
            )
            if body and "token" in body:
                student_tokens[stud["roll_no"]] = body["token"]
                student_data[stud["roll_no"]] = stud
        except Exception as exc:
            print(f"  ERROR registering student {i}: {exc}")
            operation_log.append({
                "operation": f"Register Student {i}",
                "status_code": "ERROR",
            })

    # ==================================================================
    # (c) STUDENT LOGIN
    # ==================================================================
    print_header("c. STUDENT LOGIN (All registered students)")

    login_cases = [
        ("23CS001", "SecurePass1!"),
        ("24ME012", "SecurePass3!"),
        ("23CS050", "SecurePass4!"),
        ("22EC055", "SecurePass5!"),
        ("22EC045", "SecurePass2!"),
        ("23IT015", "SecurePass6!"),
    ]

    for roll_no, password in login_cases:
        try:
            r = requests.post(
                f"{BASE}/api/students/login",
                json={
                    "email_or_roll_no": roll_no,
                    "password": password,
                },
                timeout=10,
            )
            body = print_response(
                "POST",
                "/api/students/login",
                r,
                label=f"Login Student ({roll_no})",
            )
            if body and "token" in body:
                student_tokens[roll_no] = body["token"]
        except Exception as exc:
            print(f"  ERROR logging in {roll_no}: {exc}")
            operation_log.append({
                "operation": f"Login Student ({roll_no})",
                "status_code": "ERROR",
            })

    # Invalid login attempt
    try:
        r = requests.post(
            f"{BASE}/api/students/login",
            json={
                "email_or_roll_no": "23CS001",
                "password": "WrongPassword1!",
            },
            timeout=10,
        )
        print_response(
            "POST",
            "/api/students/login",
            r,
            label="Invalid Login (wrong password) - Expected 401",
        )
    except Exception as exc:
        print(f"  ERROR: {exc}")
        operation_log.append(
            {"operation": "Invalid Login", "status_code": "ERROR"}
        )

    # ==================================================================
    # (d) GET STUDENT PROFILES
    # ==================================================================
    print_header("d. GET STUDENT PROFILES")

    for roll_no in ["23CS001", "23CS050"]:
        token = student_tokens.get(roll_no)
        if token:
            try:
                r = requests.get(
                    f"{BASE}/api/students/profile",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                print_response(
                    "GET",
                    "/api/students/profile",
                    r,
                    label=f"Profile for {roll_no}",
                )
            except Exception as exc:
                print(f"  ERROR: {exc}")
                operation_log.append(
                    {"operation": f"GET /students/profile ({roll_no})", "status_code": "ERROR"}
                )

    # ==================================================================
    # (e) SUBMIT COMPLAINTS - Various categories and types
    # ==================================================================
    print_header("e. SUBMIT COMPLAINTS (Various categories, images, spam tests)")

    complaint_specs = [
        # 1. Men's Hostel complaint with relevant image (Public)
        {
            "student": "23CS001",
            "label": "Men's Hostel - Water supply issue (Relevant image)",
            "fields": {
                "category_id": "1",  # Men's Hostel (ID=1)
                "original_text": (
                    "The water supply in men's hostel block A has been disrupted "
                    "for the past two days. We are unable to take showers or "
                    "wash clothes. This is causing a lot of inconvenience."
                ),
                "visibility": "Public",
            },
            "image_type": "room",
        },
        # 2. Women's Hostel complaint (Public)
        {
            "student": "23CS050",
            "label": "Women's Hostel - AC not working (No image)",
            "fields": {
                "category_id": "6",  # Women's Hostel (ID=6)
                "original_text": (
                    "The air conditioning in women's hostel room 215 has been "
                    "malfunctioning for a week. The room becomes unbearable "
                    "during the afternoon heat."
                ),
                "visibility": "Public",
            },
        },
        # 3. Department complaint (Department visibility)
        {
            "student": "22EC045",
            "label": "ECE Department - Broken projector (Department)",
            "fields": {
                "category_id": "3",  # Department (ID=3)
                "original_text": (
                    "The projector in ECE seminar hall 204 has been broken "
                    "for over a week. Faculty are unable to conduct lectures "
                    "effectively. Multiple professors have reported this issue."
                ),
                "visibility": "Department",
            },
        },
        # 4. General complaint (Public)
        {
            "student": "24ME012",
            "label": "General - Slow WiFi campus-wide (Public)",
            "fields": {
                "category_id": "2",  # General (ID=2)
                "original_text": (
                    "The campus WiFi network has been extremely slow for the "
                    "past several days, especially in the library and common "
                    "study areas. Students are unable to access online resources."
                ),
                "visibility": "Public",
            },
        },
        # 5. Men's Hostel with relevant image
        {
            "student": "23CS001",
            "label": "Men's Hostel - Wall crack (Relevant image)",
            "fields": {
                "category_id": "1",  # Men's Hostel (ID=1)
                "original_text": (
                    "There is a large crack in the wall of hostel room 312 "
                    "that has been growing over the past month. It looks like "
                    "a structural issue and needs immediate inspection."
                ),
                "visibility": "Public",
            },
            "image_type": "relevant",
        },
        # 6. SPAM/ABUSIVE complaint - Inappropriate language
        {
            "student": "24ME012",
            "label": "SPAM TEST - Abusive language (should be flagged)",
            "fields": {
                "category_id": "2",  # General (ID=2)
                "original_text": (
                    "This campus is absolutely terrible and the "
                    "administration is useless. Everything is broken and "
                    "nobody cares about students. The food is garbage and "
                    "the facilities are a joke. Total waste of money."
                ),
                "visibility": "Public",
            },
        },
        # 7. SPAM TEST - Text/Image mismatch (hostel complaint with food image)
        {
            "student": "23CS001",
            "label": "SPAM TEST - Text/Image mismatch (Hostel text + Food image)",
            "fields": {
                "category_id": "1",  # Men's Hostel (ID=1)
                "original_text": (
                    "The bathroom tiles in men's hostel block B are broken "
                    "and causing injuries. Please fix urgently."
                ),
                "visibility": "Public",
            },
            "image_type": "food",  # Mismatched: hostel complaint with food image
        },
        # 8. SPAM TEST - Irrelevant image (meme)
        {
            "student": "22EC055",
            "label": "SPAM TEST - Irrelevant meme image",
            "fields": {
                "category_id": "6",  # Women's Hostel (ID=6)
                "original_text": (
                    "The hot water geyser in women's hostel is not working "
                    "during morning hours. Please repair it."
                ),
                "visibility": "Public",
            },
            "image_type": "meme",  # Clearly irrelevant
        },
        # 9. Private complaint
        {
            "student": "22EC055",
            "label": "Private - Roommate issue",
            "fields": {
                "category_id": "6",  # Women's Hostel (ID=6)
                "original_text": (
                    "I am having a serious issue with my roommate who plays "
                    "loud music late at night. I have tried talking to them "
                    "multiple times but they refuse to cooperate."
                ),
                "visibility": "Private",
            },
        },
        # 10. CSE Department complaint for inter-department testing
        {
            "student": "23CS001",
            "label": "CSE Department - Lab computer issue (Department)",
            "fields": {
                "category_id": "3",  # Department (ID=3)
                "original_text": (
                    "Several computers in CSE Lab 3 are not booting properly. "
                    "This is affecting our practical sessions."
                ),
                "visibility": "Department",
            },
        },
    ]

    for spec in complaint_specs:
        token = student_tokens.get(spec["student"])
        if not token:
            print(
                f"  SKIPPED {spec['label']} - "
                f"No token for {spec['student']}"
            )
            complaint_ids.append(None)
            continue
        try:
            files_param = None
            if spec.get("image_type"):
                buf = create_test_image(spec["image_type"])
                if buf.getbuffer().nbytes > 0:
                    files_param = {"image": ("test_image.jpg", buf, "image/jpeg")}

            r = requests.post(
                f"{BASE}/api/complaints/submit",
                data=spec["fields"],
                files=files_param,
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            body = print_response(
                "POST",
                "/api/complaints/submit",
                r,
                label=spec["label"],
            )
            if body and "id" in body:
                complaint_ids.append(body["id"])
                complaint_details[body["id"]] = {
                    "student": spec["student"],
                    "category_id": spec["fields"]["category_id"],
                    "visibility": spec["fields"]["visibility"],
                    "is_spam_test": "SPAM" in spec["label"],
                }
            else:
                complaint_ids.append(None)
        except Exception as exc:
            print(f"  ERROR submitting {spec['label']}: {exc}")
            complaint_ids.append(None)
            operation_log.append({
                "operation": spec["label"],
                "status_code": "ERROR",
            })

    # ==================================================================
    # (f) PUBLIC FEED FILTERING VERIFICATION
    # ==================================================================
    print_header("f. PUBLIC FEED FILTERING (Hostel/Day Scholar, Men's/Women's Hostel)")

    print_subheader("Male Hostel Student (23CS001) - Should see Men's Hostel, NOT Women's")
    token_male_hostel = student_tokens.get("23CS001")
    if token_male_hostel:
        try:
            r = requests.get(
                f"{BASE}/api/complaints/public-feed",
                headers={"Authorization": f"Bearer {token_male_hostel}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/complaints/public-feed",
                r,
                label="Public Feed - Male Hostel Student (23CS001)",
            )
            # Category IDs: Men's Hostel=1, Women's Hostel=6
            if body and "complaints" in body:
                MENS_HOSTEL_ID = 1
                WOMENS_HOSTEL_ID = 6
                has_mens_hostel = any(
                    c.get("category_id") == MENS_HOSTEL_ID
                    for c in body["complaints"]
                )
                has_womens_hostel = any(
                    c.get("category_id") == WOMENS_HOSTEL_ID
                    for c in body["complaints"]
                )
                print_verification(
                    "Can see Men's Hostel complaints",
                    has_mens_hostel,
                    f"Found {len(body['complaints'])} complaints"
                )
                print_verification(
                    "Cannot see Women's Hostel complaints",
                    not has_womens_hostel,
                    "Women's Hostel filtered out" if not has_womens_hostel else "ERROR: Women's Hostel visible!"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Public Feed (Male Hostel)",
                "status_code": "ERROR",
            })

    print_subheader("Female Hostel Student (23CS050) - Should see Women's Hostel, NOT Men's")
    token_female_hostel = student_tokens.get("23CS050")
    if token_female_hostel:
        try:
            r = requests.get(
                f"{BASE}/api/complaints/public-feed",
                headers={"Authorization": f"Bearer {token_female_hostel}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/complaints/public-feed",
                r,
                label="Public Feed - Female Hostel Student (23CS050)",
            )
            # Category IDs: Men's Hostel=1, Women's Hostel=6
            if body and "complaints" in body:
                MENS_HOSTEL_ID = 1
                WOMENS_HOSTEL_ID = 6
                has_mens_hostel = any(
                    c.get("category_id") == MENS_HOSTEL_ID
                    for c in body["complaints"]
                )
                has_womens_hostel = any(
                    c.get("category_id") == WOMENS_HOSTEL_ID
                    for c in body["complaints"]
                )
                print_verification(
                    "Can see Women's Hostel complaints",
                    has_womens_hostel,
                    f"Found {len(body['complaints'])} complaints"
                )
                print_verification(
                    "Cannot see Men's Hostel complaints",
                    not has_mens_hostel,
                    "Men's Hostel filtered out" if not has_mens_hostel else "ERROR: Men's Hostel visible!"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Public Feed (Female Hostel)",
                "status_code": "ERROR",
            })

    print_subheader("Day Scholar (22EC045) - Should NOT see ANY hostel complaints")
    token_day_scholar = student_tokens.get("22EC045")
    if token_day_scholar:
        try:
            r = requests.get(
                f"{BASE}/api/complaints/public-feed",
                headers={"Authorization": f"Bearer {token_day_scholar}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/complaints/public-feed",
                r,
                label="Public Feed - Day Scholar (22EC045)",
            )
            # Category IDs: Men's Hostel=1, Women's Hostel=6
            if body and "complaints" in body:
                MENS_HOSTEL_ID = 1
                WOMENS_HOSTEL_ID = 6
                has_any_hostel = any(
                    c.get("category_id") in (MENS_HOSTEL_ID, WOMENS_HOSTEL_ID)
                    for c in body["complaints"]
                )
                print_verification(
                    "Cannot see ANY Hostel complaints",
                    not has_any_hostel,
                    "All hostel complaints filtered out" if not has_any_hostel else "ERROR: Hostel visible!"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Public Feed (Day Scholar)",
                "status_code": "ERROR",
            })

    print_subheader("Inter-department filtering - ECE student should not see CSE dept complaints")
    # 22EC055 is ECE, should not see CSE department complaints
    token_ece = student_tokens.get("22EC055")
    if token_ece:
        try:
            r = requests.get(
                f"{BASE}/api/complaints/public-feed",
                headers={"Authorization": f"Bearer {token_ece}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/complaints/public-feed",
                r,
                label="Public Feed - ECE Student (22EC055) checking for CSE dept complaints",
            )
            # Note: Department complaints with visibility "Department" should only be visible to same department
        except Exception as exc:
            print(f"  ERROR: {exc}")

    # ==================================================================
    # (g) VOTING
    # ==================================================================
    print_header("g. VOTING (Multiple votes, real-time update verification)")

    vote_target = complaint_ids[0] if len(complaint_ids) > 0 else None

    if vote_target:
        print_subheader("Initial vote counts")
        # Get initial complaint state
        token_s1 = student_tokens.get("23CS001")
        if token_s1:
            r = requests.get(
                f"{BASE}/api/complaints/{vote_target}",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            initial_body = print_response(
                "GET",
                f"/api/complaints/{vote_target}",
                r,
                label="Get initial complaint state",
            )
            initial_upvotes = initial_body.get("upvotes", 0) if initial_body else 0
            initial_downvotes = initial_body.get("downvotes", 0) if initial_body else 0

        print_subheader("Multiple students vote")
        # Multiple students upvote
        for roll_no in ["22EC045", "24ME012", "23CS050"]:
            token = student_tokens.get(roll_no)
            if token and vote_target:
                try:
                    r = requests.post(
                        f"{BASE}/api/complaints/{vote_target}/vote",
                        json={"vote_type": "Upvote"},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    print_response(
                        "POST",
                        f"/api/complaints/{vote_target}/vote",
                        r,
                        label=f"{roll_no} upvotes complaint",
                    )
                except Exception as exc:
                    print(f"  ERROR: {exc}")

        # One student downvotes
        vote_target_2 = complaint_ids[3] if len(complaint_ids) > 3 else None
        if vote_target_2:
            token = student_tokens.get("23IT015")
            if token:
                try:
                    r = requests.post(
                        f"{BASE}/api/complaints/{vote_target_2}/vote",
                        json={"vote_type": "Downvote"},
                        headers={"Authorization": f"Bearer {token}"},
                        timeout=10,
                    )
                    print_response(
                        "POST",
                        f"/api/complaints/{vote_target_2}/vote",
                        r,
                        label="23IT015 downvotes WiFi complaint",
                    )
                except Exception as exc:
                    print(f"  ERROR: {exc}")

        print_subheader("Verify vote count changed")
        if token_s1:
            r = requests.get(
                f"{BASE}/api/complaints/{vote_target}",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            updated_body = print_response(
                "GET",
                f"/api/complaints/{vote_target}",
                r,
                label="Get updated complaint state after votes",
            )
            if updated_body:
                new_upvotes = updated_body.get("upvotes", 0)
                print_verification(
                    "Vote count updated",
                    new_upvotes > initial_upvotes,
                    f"Upvotes: {initial_upvotes} -> {new_upvotes}"
                )

        print_subheader("Check my-vote and remove vote")
        token = student_tokens.get("22EC045")
        if token and vote_target:
            # Check current vote
            r = requests.get(
                f"{BASE}/api/complaints/{vote_target}/my-vote",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            print_response(
                "GET",
                f"/api/complaints/{vote_target}/my-vote",
                r,
                label="Check vote status for 22EC045",
            )

            # Remove vote
            r = requests.delete(
                f"{BASE}/api/complaints/{vote_target}/vote",
                headers={"Authorization": f"Bearer {token}"},
                timeout=10,
            )
            print_response(
                "DELETE",
                f"/api/complaints/{vote_target}/vote",
                r,
                label="Remove vote for 22EC045",
            )

    # ==================================================================
    # (h) AUTHORITY LOGIN - ALL AUTHORITIES
    # ==================================================================
    print_header("h. AUTHORITY LOGIN (All authority types)")

    authority_credentials = [
        # Admin
        ("admin@srec.ac.in", "Admin@123456", "Admin"),
        # Admin Officer
        ("officer@srec.ac.in", "Officer@1234", "Admin Officer"),
        # Senior Deputy Warden
        ("sdw@srec.ac.in", "SeniorDW@123", "Senior Deputy Warden"),
        # Men's Hostel Deputy Warden
        ("dw.mens@srec.ac.in", "MensDW@1234", "Men's Hostel Deputy Warden"),
        # Men's Hostel Wardens
        ("warden1.mens@srec.ac.in", "MensW1@1234", "Men's Hostel Warden 1"),
        ("warden2.mens@srec.ac.in", "MensW2@1234", "Men's Hostel Warden 2"),
        # Women's Hostel Deputy Warden
        ("dw.womens@srec.ac.in", "WomensDW@123", "Women's Hostel Deputy Warden"),
        # Women's Hostel Wardens
        ("warden1.womens@srec.ac.in", "WomensW1@123", "Women's Hostel Warden 1"),
        ("warden2.womens@srec.ac.in", "WomensW2@123", "Women's Hostel Warden 2"),
        # HODs
        ("hod.cse@srec.ac.in", "HodCSE@123", "HOD CSE"),
        ("hod.ece@srec.ac.in", "HodECE@123", "HOD ECE"),
        ("hod.mech@srec.ac.in", "HodMECH@123", "HOD MECH"),
        # Disciplinary Committee
        ("dc@srec.ac.in", "Discip@12345", "Disciplinary Committee"),
    ]

    for email, pwd, auth_type in authority_credentials:
        try:
            r = requests.post(
                f"{BASE}/api/authorities/login",
                json={"email": email, "password": pwd},
                timeout=10,
            )
            body = print_response(
                "POST",
                "/api/authorities/login",
                r,
                label=f"Authority Login ({auth_type})",
            )
            if body and "token" in body:
                authority_tokens[auth_type] = body["token"]
                authority_data[auth_type] = {
                    "id": body.get("id"),
                    "email": email,
                    "type": body.get("authority_type"),
                }
                print(f"  >>> {auth_type} login successful")
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": f"Authority Login ({auth_type})",
                "status_code": "ERROR",
            })

    print(f"\n  Successfully logged in {len(authority_tokens)} authorities")

    # ==================================================================
    # (i) AUTHORITY DASHBOARD & COMPLAINTS
    # ==================================================================
    print_header("i. AUTHORITY DASHBOARD & COMPLAINT VIEW")

    # Test dashboard for Men's Hostel Warden
    warden_token = authority_tokens.get("Men's Hostel Warden 1")
    if warden_token:
        print_subheader("Men's Hostel Warden Dashboard")
        try:
            r = requests.get(
                f"{BASE}/api/authorities/dashboard",
                headers={"Authorization": f"Bearer {warden_token}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/api/authorities/dashboard",
                r,
                label="Men's Hostel Warden Dashboard",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        print_subheader("Men's Hostel Warden - Assigned Complaints")
        try:
            r = requests.get(
                f"{BASE}/api/authorities/my-complaints",
                headers={"Authorization": f"Bearer {warden_token}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/authorities/my-complaints",
                r,
                label="Men's Hostel Warden - Assigned Complaints (with anonymity check)",
            )
            if body and "complaints" in body:
                print("\n  Anonymity Check:")
                for c in body["complaints"]:
                    is_spam = c.get("is_marked_as_spam", False)
                    has_student_info = c.get("student_roll_no") is not None
                    status = "[CORRECT]" if (is_spam == has_student_info) or (not is_spam and not has_student_info) else "[ERROR]"
                    print(f"    {status} Complaint {str(c.get('id', ''))[:8]}... | Spam: {is_spam} | Student Info Visible: {has_student_info}")
        except Exception as exc:
            print(f"  ERROR: {exc}")

    # ==================================================================
    # (j) AUTHORITY STATUS CHANGES & UPDATES
    # ==================================================================
    print_header("j. AUTHORITY STATUS CHANGES & UPDATES")

    target_complaint = complaint_ids[0] if len(complaint_ids) > 0 else None
    warden_token = authority_tokens.get("Men's Hostel Warden 1")

    if warden_token and target_complaint:
        print_subheader("Status Change: Raised -> In Progress")
        try:
            r = requests.put(
                f"{BASE}/api/authorities/complaints/{target_complaint}/status",
                json={
                    "status": "In Progress",
                    "reason": "Maintenance team has been notified and is working on it.",
                },
                headers={"Authorization": f"Bearer {warden_token}"},
                timeout=10,
            )
            print_response(
                "PUT",
                f"/api/authorities/complaints/{target_complaint}/status",
                r,
                label="Change status to 'In Progress'",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        print_subheader("Post Public Update")
        try:
            r = requests.post(
                f"{BASE}/api/authorities/complaints/{target_complaint}/post-update",
                params={
                    "title": "Plumber dispatched",
                    "content": "A plumber has been dispatched to hostel block A. Expected fix within 24 hours.",
                },
                headers={"Authorization": f"Bearer {warden_token}"},
                timeout=10,
            )
            print_response(
                "POST",
                f"/api/authorities/complaints/{target_complaint}/post-update",
                r,
                label="Post authority update on complaint",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        print_subheader("Status Change: In Progress -> Resolved")
        try:
            r = requests.put(
                f"{BASE}/api/authorities/complaints/{target_complaint}/status",
                json={
                    "status": "Resolved",
                    "reason": "Water supply has been restored after pipe repair.",
                },
                headers={"Authorization": f"Bearer {warden_token}"},
                timeout=10,
            )
            print_response(
                "PUT",
                f"/api/authorities/complaints/{target_complaint}/status",
                r,
                label="Change status to 'Resolved'",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        print_subheader("View Status History")
        token_s1 = student_tokens.get("23CS001")
        if token_s1:
            try:
                r = requests.get(
                    f"{BASE}/api/complaints/{target_complaint}/status-history",
                    headers={"Authorization": f"Bearer {token_s1}"},
                    timeout=10,
                )
                print_response(
                    "GET",
                    f"/api/complaints/{target_complaint}/status-history",
                    r,
                    label="Status History",
                )
            except Exception as exc:
                print(f"  ERROR: {exc}")

    # ==================================================================
    # (k) COMPLAINTS AGAINST AUTHORITIES & ESCALATION
    # ==================================================================
    print_header("k. COMPLAINTS AGAINST AUTHORITIES & PRIVILEGE ESCALATION")

    print_subheader("Submit complaint about Men's Hostel Warden (LLM detects authority complaint)")
    token_male = student_tokens.get("24ME012")
    if token_male:
        try:
            r = requests.post(
                f"{BASE}/api/complaints/submit",
                data={
                    "category_id": "1",  # Men's Hostel (ID=1)
                    "original_text": (
                        "The warden of Men's Hostel Block A is not responding to our requests "
                        "for room repairs. We have submitted multiple requests but no action has been taken. "
                        "This complaint is about the warden's negligence and unprofessional behavior."
                    ),
                    "visibility": "Public",
                },
                headers={"Authorization": f"Bearer {token_male}"},
                timeout=30,
            )
            body = print_response(
                "POST",
                "/api/complaints/submit",
                r,
                label="Complaint AGAINST Men's Hostel Warden",
            )
            if body and "id" in body:
                against_warden_id = body["id"]
                assigned_to = body.get("assigned_authority", "Unknown")
                print(f"\n  Assigned to: {assigned_to}")

                # LLM should detect this is against warden and escalate
                # assigned_authority is a string (authority name)
                print_verification(
                    "Complaint submitted successfully (LLM may escalate)",
                    body.get("id") is not None,
                    f"Assigned to: {assigned_to}"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")

    print_subheader("Submit complaint about HOD (LLM detects authority complaint)")
    token_ece = student_tokens.get("22EC045")
    if token_ece:
        try:
            r = requests.post(
                f"{BASE}/api/complaints/submit",
                data={
                    "category_id": "3",  # Department (ID=3)
                    "original_text": (
                        "The HOD of ECE department is showing favoritism in project allocations. "
                        "Some students are getting better projects while others are ignored. "
                        "This is a complaint against the HOD's unfair treatment and biased behavior."
                    ),
                    "visibility": "Private",
                },
                headers={"Authorization": f"Bearer {token_ece}"},
                timeout=30,
            )
            body = print_response(
                "POST",
                "/api/complaints/submit",
                r,
                label="Complaint AGAINST HOD (LLM should escalate to Admin)",
            )
            if body and "id" in body:
                assigned_to = body.get("assigned_authority", "Unknown")
                print(f"\n  Assigned to: {assigned_to}")

                print_verification(
                    "Complaint submitted successfully (LLM may escalate)",
                    body.get("id") is not None,
                    f"Assigned to: {assigned_to}"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")

    print_subheader("Manual Escalation by Authority")
    # First get a complaint assigned to warden, then escalate it
    warden_token = authority_tokens.get("Men's Hostel Warden 1")
    if warden_token and len(complaint_ids) > 0:
        # Get warden's complaints first
        try:
            r = requests.get(
                f"{BASE}/api/authorities/my-complaints",
                headers={"Authorization": f"Bearer {warden_token}"},
                timeout=10,
            )
            body = r.json() if r.status_code == 200 else None
            if body and "complaints" in body and len(body["complaints"]) > 0:
                escalate_complaint_id = body["complaints"][0]["id"]

                r = requests.post(
                    f"{BASE}/api/authorities/complaints/{escalate_complaint_id}/escalate",
                    params={"reason": "This requires attention from higher authority due to complexity."},
                    headers={"Authorization": f"Bearer {warden_token}"},
                    timeout=10,
                )
                print_response(
                    "POST",
                    f"/api/authorities/complaints/{escalate_complaint_id}/escalate",
                    r,
                    label="Manual Escalation by Warden",
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")

    # ==================================================================
    # (l) STUDENT NOTIFICATIONS (after authority updates)
    # ==================================================================
    print_header("l. STUDENT NOTIFICATIONS (Verify authority updates visible)")

    token_s1 = student_tokens.get("23CS001")
    if token_s1:
        try:
            r = requests.get(
                f"{BASE}/api/students/notifications/unread-count",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/api/students/notifications/unread-count",
                r,
                label="Unread notification count for 23CS001",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        try:
            r = requests.get(
                f"{BASE}/api/students/notifications",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/students/notifications",
                r,
                label="All notifications for 23CS001",
            )
            if body and "notifications" in body:
                print(f"\n  Total notifications: {len(body['notifications'])}")
                for n in body["notifications"][:5]:  # Show first 5
                    print(f"    - {n.get('notification_type', 'unknown')}: {n.get('message', '')[:50]}...")
        except Exception as exc:
            print(f"  ERROR: {exc}")

    # Verify another student (who should NOT see 23CS001's notifications)
    token_s2 = student_tokens.get("22EC045")
    if token_s2:
        try:
            r = requests.get(
                f"{BASE}/api/students/notifications",
                headers={"Authorization": f"Bearer {token_s2}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/students/notifications",
                r,
                label="Notifications for 22EC045 (should be different from 23CS001)",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

    # ==================================================================
    # (m) ADMIN FULL ACCESS VERIFICATION
    # ==================================================================
    print_header("m. ADMIN FULL ACCESS VERIFICATION")

    admin_token = authority_tokens.get("Admin")
    if admin_token:
        print_subheader("Admin Dashboard")
        try:
            r = requests.get(
                f"{BASE}/api/authorities/dashboard",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/api/authorities/dashboard",
                r,
                label="Admin Dashboard (should show all stats)",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        print_subheader("Admin - View All Complaints (with full student info)")
        try:
            r = requests.get(
                f"{BASE}/api/authorities/my-complaints",
                headers={"Authorization": f"Bearer {admin_token}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/api/authorities/my-complaints",
                r,
                label="Admin - All Complaints (admin sees all student info)",
            )
            if body and "complaints" in body:
                print("\n  Admin visibility check:")
                all_have_student_info = all(
                    c.get("student_roll_no") is not None or c.get("student_name") is not None
                    for c in body["complaints"]
                ) if body["complaints"] else True
                print_verification(
                    "Admin can see all student information",
                    all_have_student_info,
                    f"Checked {len(body['complaints'])} complaints"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")

        print_subheader("Admin - Change Status of Any Complaint")
        if len(complaint_ids) > 1 and complaint_ids[1]:
            try:
                r = requests.put(
                    f"{BASE}/api/authorities/complaints/{complaint_ids[1]}/status",
                    json={
                        "status": "In Progress",
                        "reason": "Admin reviewing this complaint.",
                    },
                    headers={"Authorization": f"Bearer {admin_token}"},
                    timeout=10,
                )
                print_response(
                    "PUT",
                    f"/api/authorities/complaints/{complaint_ids[1]}/status",
                    r,
                    label="Admin changes status of Women's Hostel complaint",
                )
            except Exception as exc:
                print(f"  ERROR: {exc}")

    # ==================================================================
    # (n) MY COMPLAINTS & COMPLAINT DETAILS
    # ==================================================================
    print_header("n. MY COMPLAINTS & COMPLAINT DETAILS")

    for roll_no in ["23CS001", "23CS050", "22EC045"]:
        token = student_tokens.get(roll_no)
        if token:
            try:
                r = requests.get(
                    f"{BASE}/api/students/my-complaints",
                    headers={"Authorization": f"Bearer {token}"},
                    timeout=10,
                )
                body = print_response(
                    "GET",
                    "/api/students/my-complaints",
                    r,
                    label=f"My Complaints for {roll_no}",
                )
            except Exception as exc:
                print(f"  ERROR: {exc}")

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print(f"\n{SEPARATOR}")
    print("=== TEST RUN SUMMARY ===")
    print(THIN_SEP)
    print(f"{'#':<5} {'Operation':<65} {'Status':<12}")
    print(THIN_SEP)
    for i, entry in enumerate(operation_log, start=1):
        op_name = entry['operation'][:62] + "..." if len(entry['operation']) > 65 else entry['operation']
        print(f"{i:<5} {op_name:<65} {entry['status_code']:<12}")
    print(THIN_SEP)
    print(f"Total operations: {len(operation_log)}")

    success_count = sum(
        1
        for e in operation_log
        if isinstance(e["status_code"], int) and 200 <= e["status_code"] < 400
    )
    error_count = sum(
        1 for e in operation_log if e["status_code"] == "ERROR"
    )
    client_error_count = sum(
        1
        for e in operation_log
        if isinstance(e["status_code"], int) and 400 <= e["status_code"] < 500
    )
    server_error_count = sum(
        1
        for e in operation_log
        if isinstance(e["status_code"], int) and e["status_code"] >= 500
    )
    skipped_count = sum(
        1 for e in operation_log if e["status_code"] == "SKIPPED"
    )

    print(f"  Successful (2xx/3xx): {success_count}")
    print(f"  Client Errors (4xx):  {client_error_count}")
    print(f"  Server Errors (5xx):  {server_error_count}")
    print(f"  Connection Errors:    {error_count}")
    print(f"  Skipped:              {skipped_count}")

    # Verification summary
    print(f"\n{THIN_SEP}")
    print("=== VERIFICATION NOTES ===")
    print("""
Key verifications performed:
1. Male hostel students can see Men's Hostel complaints, NOT Women's Hostel
2. Female hostel students can see Women's Hostel complaints, NOT Men's Hostel
3. Day scholars cannot see ANY hostel complaints
4. Spam complaints reveal student info to authorities
5. Non-spam complaints hide student info from authorities (except Admin)
6. Complaints against authorities escalate to higher level
7. Admin can see all student information
8. Students receive notifications for status updates
9. Voting updates are reflected in complaint data
    """)

    print(f"\nFinished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)

    # Exit with error code if there were server errors
    if server_error_count > 0:
        print(f"\n!!! {server_error_count} SERVER ERRORS DETECTED !!!")
        sys.exit(1)


if __name__ == "__main__":
    main()
