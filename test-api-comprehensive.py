"""
CampusVoice API - Comprehensive End-to-End Test Script

This script exercises the full CampusVoice API sequentially, printing actual
API responses for each operation. It serves as both a verification tool and a
demo of the entire system.

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
from typing import Optional

import requests

# ---------------------------------------------------------------------------
# Formatting helpers
# ---------------------------------------------------------------------------

SEPARATOR = "=" * 60
THIN_SEP = "-" * 60

# Collected summary of all operations
operation_log: list[dict] = []


def print_header(title: str) -> None:
    """Print a section header."""
    print(f"\n{SEPARATOR}")
    print(f"=== {title} ===")
    print(THIN_SEP)


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
    status = response.status_code
    print(f"Endpoint: {method} {path}")
    print()

    body = None
    try:
        body = response.json()
        print(f"[Status Code: {status}]")
        print("Response:")
        print(json.dumps(body, indent=2, default=str))
    except Exception:
        print(f"[Status Code: {status}]")
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
    operation_log.append({"operation": tag, "status_code": status})
    return body


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
    student_tokens: dict[str, str] = {}       # roll_no -> token
    complaint_ids: list[Optional[str]] = []   # ordered list of complaint UUIDs
    authority_token: Optional[str] = None
    authority_id: Optional[int] = None
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
    # (b) STUDENT REGISTRATION (4 students)
    # ==================================================================
    print_header("b. STUDENT REGISTRATION")

    students = [
        {
            "roll_no": "23CS001",
            "name": "Arjun Kumar",
            "email": "arjun.kumar@college.edu",
            "password": "SecurePass1!",
            "gender": "Male",
            "stay_type": "Hostel",
            "department_id": 1,
            "year": 2,
        },
        {
            "roll_no": "22EC045",
            "name": "Priya Sharma",
            "email": "priya.sharma@college.edu",
            "password": "SecurePass2!",
            "gender": "Female",
            "stay_type": "Day Scholar",
            "department_id": 2,
            "year": 3,
        },
        {
            "roll_no": "24ME012",
            "name": "Rahul Verma",
            "email": "rahul.verma@college.edu",
            "password": "SecurePass3!",
            "gender": "Male",
            "stay_type": "Hostel",
            "department_id": 4,
            "year": 1,
        },
        {
            "roll_no": "23CS050",
            "name": "Deepa Nair",
            "email": "deepa.nair@college.edu",
            "password": "SecurePass4!",
            "gender": "Female",
            "stay_type": "Hostel",
            "department_id": 1,
            "year": 2,
        },
    ]

    for i, student_data in enumerate(students, start=1):
        try:
            r = requests.post(
                f"{BASE}/students/register",
                json=student_data,
                timeout=15,
            )
            body = print_response(
                "POST",
                "/students/register",
                r,
                label=f"Register Student {i} ({student_data['roll_no']})",
            )
            if body and "token" in body:
                student_tokens[student_data["roll_no"]] = body["token"]
        except Exception as exc:
            print(f"  ERROR registering student {i}: {exc}")
            operation_log.append({
                "operation": f"Register Student {i}",
                "status_code": "ERROR",
            })

    # ==================================================================
    # (c) STUDENT LOGIN (all 4 + invalid attempt)
    # ==================================================================
    print_header("c. STUDENT LOGIN")

    login_cases = [
        ("23CS001", "SecurePass1!"),
        ("22EC045", "SecurePass2!"),
        ("24ME012", "SecurePass3!"),
        ("23CS050", "SecurePass4!"),
    ]

    for roll_no, password in login_cases:
        try:
            r = requests.post(
                f"{BASE}/students/login",
                json={
                    "email_or_roll_no": roll_no,
                    "password": password,
                },
                timeout=10,
            )
            body = print_response(
                "POST",
                "/students/login",
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
            f"{BASE}/students/login",
            json={
                "email_or_roll_no": "23CS001",
                "password": "WrongPassword1!",
            },
            timeout=10,
        )
        print_response(
            "POST",
            "/students/login",
            r,
            label="Invalid Login (wrong password)",
        )
    except Exception as exc:
        print(f"  ERROR: {exc}")
        operation_log.append(
            {"operation": "Invalid Login", "status_code": "ERROR"}
        )

    # ==================================================================
    # (d) GET STUDENT PROFILE
    # ==================================================================
    print_header("d. GET STUDENT PROFILE")

    token_s1 = student_tokens.get("23CS001")
    if token_s1:
        try:
            r = requests.get(
                f"{BASE}/students/profile",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/students/profile",
                r,
                label="Profile for Student 1 (23CS001)",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append(
                {"operation": "GET /students/profile", "status_code": "ERROR"}
            )
    else:
        print("  SKIPPED - No token for Student 1")

    # ==================================================================
    # (e) SUBMIT COMPLAINTS (6 complaints)
    # ==================================================================
    print_header("e. SUBMIT COMPLAINTS")

    complaint_specs = [
        {
            "student": "23CS001",
            "label": "Complaint 1 - Hostel water supply (Public)",
            "fields": {
                "category_id": "1",
                "original_text": (
                    "The water supply in hostel block A has been disrupted "
                    "for the past two days. We are unable to take showers or "
                    "wash clothes. This is causing a lot of inconvenience to "
                    "all residents."
                ),
                "visibility": "Public",
            },
        },
        {
            "student": "22EC045",
            "label": "Complaint 2 - Broken projector in ECE (Department)",
            "fields": {
                "category_id": "3",
                "original_text": (
                    "The projector in ECE seminar hall 204 has been broken "
                    "for over a week. Faculty are unable to conduct lectures "
                    "effectively. Multiple professors have reported this issue."
                ),
                "visibility": "Department",
            },
        },
        {
            "student": "24ME012",
            "label": "Complaint 3 - Slow WiFi campus-wide (Public)",
            "fields": {
                "category_id": "2",
                "original_text": (
                    "The campus WiFi network has been extremely slow for the "
                    "past several days, especially in the library and common "
                    "study areas. Students are unable to access online "
                    "resources or submit assignments on time."
                ),
                "visibility": "Public",
            },
        },
        {
            "student": "23CS001",
            "label": "Complaint 4 - Wall crack needing image (Public)",
            "fields": {
                "category_id": "1",
                "original_text": (
                    "There is a large crack in the wall of hostel room 312 "
                    "that has been growing over the past month. It looks like "
                    "a structural issue and needs immediate inspection by the "
                    "maintenance team."
                ),
                "visibility": "Public",
            },
        },
        {
            "student": "23CS050",
            "label": "Complaint 5 - Potentially spam/abusive (Public)",
            "fields": {
                "category_id": "2",
                "original_text": (
                    "This campus is absolutely terrible and the "
                    "administration is useless. Everything is broken and "
                    "nobody cares about students. The food is garbage and "
                    "the facilities are a joke. Total waste of money."
                ),
                "visibility": "Public",
            },
        },
        {
            "student": "24ME012",
            "label": "Complaint 6 - Private roommate issue",
            "fields": {
                "category_id": "1",
                "original_text": (
                    "I am having a serious issue with my roommate who plays "
                    "loud music late at night. I have tried talking to them "
                    "multiple times but they refuse to cooperate. This is "
                    "affecting my studies and sleep."
                ),
                "visibility": "Private",
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
            r = requests.post(
                f"{BASE}/complaints/submit",
                data=spec["fields"],
                headers={"Authorization": f"Bearer {token}"},
                timeout=30,
            )
            body = print_response(
                "POST",
                "/complaints/submit",
                r,
                label=spec["label"],
            )
            if body and "id" in body:
                complaint_ids.append(body["id"])
            else:
                # Even on rejection, record a placeholder
                complaint_ids.append(None)
        except Exception as exc:
            print(f"  ERROR submitting {spec['label']}: {exc}")
            complaint_ids.append(None)
            operation_log.append({
                "operation": spec["label"],
                "status_code": "ERROR",
            })

    # ==================================================================
    # (f) IMAGE UPLOAD (for Complaint 4)
    # ==================================================================
    print_header("f. IMAGE UPLOAD (for Complaint 4)")

    complaint_4_id = complaint_ids[3] if len(complaint_ids) > 3 else None
    token_s1 = student_tokens.get("23CS001")

    if complaint_4_id and token_s1:
        try:
            from PIL import Image, ImageDraw

            img = Image.new("RGB", (200, 200), color=(180, 60, 60))
            draw = ImageDraw.Draw(img)
            draw.line(
                [(20, 20), (100, 100), (80, 180)],
                fill=(50, 50, 50),
                width=3,
            )
            draw.line(
                [(100, 100), (180, 60)],
                fill=(50, 50, 50),
                width=2,
            )
            draw.text((10, 185), "wall crack", fill=(255, 255, 255))

            buf = io.BytesIO()
            img.save(buf, format="JPEG")
            buf.seek(0)

            r = requests.post(
                f"{BASE}/complaints/{complaint_4_id}/upload-image",
                files={"file": ("wall_crack.jpg", buf, "image/jpeg")},
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=30,
            )
            print_response(
                "POST",
                f"/complaints/{complaint_4_id}/upload-image",
                r,
                label="Upload image for Complaint 4",
            )
        except ImportError:
            print(
                "  WARNING: Pillow not installed. Skipping image generation."
            )
            print("  Install with: pip install Pillow")
            operation_log.append(
                {"operation": "Image Upload", "status_code": "SKIPPED"}
            )
        except Exception as exc:
            print(f"  ERROR uploading image: {exc}")
            operation_log.append(
                {"operation": "Image Upload", "status_code": "ERROR"}
            )
    else:
        print(
            "  SKIPPED - Complaint 4 was not created or no token available."
        )
        operation_log.append(
            {"operation": "Image Upload", "status_code": "SKIPPED"}
        )

    # ==================================================================
    # (g) PUBLIC FEED - Visibility differences
    # ==================================================================
    print_header("g. PUBLIC FEED - Visibility Differences")

    # Student 1: Hostel / CSE
    token_s1 = student_tokens.get("23CS001")
    if token_s1:
        try:
            r = requests.get(
                f"{BASE}/complaints/public-feed",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/complaints/public-feed",
                r,
                label=(
                    "Public Feed as Student 1 "
                    "(23CS001 - Hostel/CSE)"
                ),
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Public Feed (Student 1)",
                "status_code": "ERROR",
            })

    # Student 2: Day Scholar / ECE
    token_s2 = student_tokens.get("22EC045")
    if token_s2:
        try:
            r = requests.get(
                f"{BASE}/complaints/public-feed",
                headers={"Authorization": f"Bearer {token_s2}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/complaints/public-feed",
                r,
                label=(
                    "Public Feed as Student 2 "
                    "(22EC045 - Day Scholar/ECE)"
                ),
            )
            if body:
                print(
                    "\n  NOTE: Day Scholar should NOT see "
                    "Hostel-category complaints."
                )
                print(
                    "        ECE student may not see CSE "
                    "department-specific complaints.\n"
                )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Public Feed (Student 2)",
                "status_code": "ERROR",
            })

    # ==================================================================
    # (h) VOTING
    # ==================================================================
    print_header("h. VOTING")

    vote_target = complaint_ids[0] if len(complaint_ids) > 0 else None
    vote_target_3 = complaint_ids[2] if len(complaint_ids) > 2 else None

    # Student 2 upvotes Complaint 1
    if vote_target and student_tokens.get("22EC045"):
        try:
            r = requests.post(
                f"{BASE}/complaints/{vote_target}/vote",
                json={"vote_type": "Upvote"},
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['22EC045']}"
                },
                timeout=10,
            )
            print_response(
                "POST",
                f"/complaints/{vote_target}/vote",
                r,
                label="Student 2 upvotes Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Student 2 upvotes Complaint 1",
                "status_code": "ERROR",
            })

    # Student 3 upvotes Complaint 1
    if vote_target and student_tokens.get("24ME012"):
        try:
            r = requests.post(
                f"{BASE}/complaints/{vote_target}/vote",
                json={"vote_type": "Upvote"},
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['24ME012']}"
                },
                timeout=10,
            )
            print_response(
                "POST",
                f"/complaints/{vote_target}/vote",
                r,
                label="Student 3 upvotes Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Student 3 upvotes Complaint 1",
                "status_code": "ERROR",
            })

    # Student 4 downvotes Complaint 3
    if vote_target_3 and student_tokens.get("23CS050"):
        try:
            r = requests.post(
                f"{BASE}/complaints/{vote_target_3}/vote",
                json={"vote_type": "Downvote"},
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['23CS050']}"
                },
                timeout=10,
            )
            print_response(
                "POST",
                f"/complaints/{vote_target_3}/vote",
                r,
                label="Student 4 downvotes Complaint 3",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Student 4 downvotes Complaint 3",
                "status_code": "ERROR",
            })

    # Check my-vote for Student 2 on Complaint 1
    if vote_target and student_tokens.get("22EC045"):
        try:
            r = requests.get(
                f"{BASE}/complaints/{vote_target}/my-vote",
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['22EC045']}"
                },
                timeout=10,
            )
            print_response(
                "GET",
                f"/complaints/{vote_target}/my-vote",
                r,
                label="Check Student 2 vote on Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Check vote status",
                "status_code": "ERROR",
            })

    # Remove Student 2's vote on Complaint 1
    if vote_target and student_tokens.get("22EC045"):
        try:
            r = requests.delete(
                f"{BASE}/complaints/{vote_target}/vote",
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['22EC045']}"
                },
                timeout=10,
            )
            print_response(
                "DELETE",
                f"/complaints/{vote_target}/vote",
                r,
                label="Remove Student 2 vote on Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Remove vote",
                "status_code": "ERROR",
            })

    # Re-check Student 2's vote (should be gone)
    if vote_target and student_tokens.get("22EC045"):
        try:
            r = requests.get(
                f"{BASE}/complaints/{vote_target}/my-vote",
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['22EC045']}"
                },
                timeout=10,
            )
            print_response(
                "GET",
                f"/complaints/{vote_target}/my-vote",
                r,
                label="Re-check Student 2 vote after removal",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Re-check vote after removal",
                "status_code": "ERROR",
            })

    # Re-check public feed to see updated vote counts
    if student_tokens.get("23CS001"):
        try:
            r = requests.get(
                f"{BASE}/complaints/public-feed",
                headers={
                    "Authorization":
                        f"Bearer {student_tokens['23CS001']}"
                },
                timeout=10,
            )
            print_response(
                "GET",
                "/complaints/public-feed",
                r,
                label="Public Feed after voting (updated vote counts)",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Public Feed after voting",
                "status_code": "ERROR",
            })

    # ==================================================================
    # (i) AUTHORITY LOGIN & DASHBOARD
    # ==================================================================
    print_header("i. AUTHORITY LOGIN & DASHBOARD")

    # Try several common authority credentials that may be seeded on startup
    authority_emails = [
        ("warden@college.edu", "SecurePass123!"),
        ("warden@campusvoice.edu", "SecurePass123!"),
        ("admin@college.edu", "SecurePass123!"),
        ("admin@campusvoice.edu", "SecurePass123!"),
        ("admin.officer@college.edu", "SecurePass123!"),
        ("hostel.warden@college.edu", "SecurePass123!"),
        ("warden@college.edu", "Warden@123"),
        ("admin@campusvoice.edu", "Admin@123"),
        ("adminofficer@college.edu", "AdminOfficer@123"),
    ]

    for email, pwd in authority_emails:
        try:
            r = requests.post(
                f"{BASE}/authorities/login",
                json={"email": email, "password": pwd},
                timeout=10,
            )
            body = print_response(
                "POST",
                "/authorities/login",
                r,
                label=f"Authority Login ({email})",
            )
            if body and "token" in body:
                authority_token = body["token"]
                authority_id = body.get("id")
                print(f"  >>> Authority login successful with {email}")
                break
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": f"Authority Login ({email})",
                "status_code": "ERROR",
            })

    if not authority_token:
        print(
            "\n  WARNING: Could not log in any authority. "
            "Authority-dependent tests will be skipped."
        )
        print(
            "  Ensure the server has seeded authority accounts on startup."
        )

    # Authority Dashboard
    if authority_token:
        try:
            r = requests.get(
                f"{BASE}/authorities/dashboard",
                headers={"Authorization": f"Bearer {authority_token}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/authorities/dashboard",
                r,
                label="Authority Dashboard",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Authority Dashboard",
                "status_code": "ERROR",
            })

    # Authority's Assigned Complaints (with partial anonymity)
    if authority_token:
        try:
            r = requests.get(
                f"{BASE}/authorities/my-complaints",
                headers={"Authorization": f"Bearer {authority_token}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/authorities/my-complaints",
                r,
                label=(
                    "Authority Assigned Complaints "
                    "(note: student info hidden for non-spam)"
                ),
            )
            if (
                body
                and isinstance(body, dict)
                and "complaints" in body
            ):
                for c in body["complaints"]:
                    anon = (
                        "HIDDEN"
                        if c.get("student_roll_no") is None
                        else "VISIBLE"
                    )
                    print(
                        f"  - Complaint {str(c.get('id', ''))[:8]}... | "
                        f"Student info: {anon} | "
                        f"Spam: {c.get('is_marked_as_spam')}"
                    )
                print()
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Authority Assigned Complaints",
                "status_code": "ERROR",
            })

    # ==================================================================
    # (j) AUTHORITY STATUS CHANGES
    # ==================================================================
    print_header("j. AUTHORITY STATUS CHANGES")

    target_complaint = (
        complaint_ids[0] if len(complaint_ids) > 0 else None
    )

    if authority_token and target_complaint:
        # Change to "In Progress"
        try:
            r = requests.put(
                f"{BASE}/authorities/complaints/"
                f"{target_complaint}/status",
                json={
                    "status": "In Progress",
                    "reason": (
                        "Maintenance team has been notified and is "
                        "working on it."
                    ),
                },
                headers={"Authorization": f"Bearer {authority_token}"},
                timeout=10,
            )
            print_response(
                "PUT",
                f"/authorities/complaints/{target_complaint}/status",
                r,
                label="Change Complaint 1 status to 'In Progress'",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Status -> In Progress",
                "status_code": "ERROR",
            })

        # Post an update
        try:
            r = requests.post(
                f"{BASE}/authorities/complaints/"
                f"{target_complaint}/post-update",
                params={
                    "title": "Plumber dispatched",
                    "content": (
                        "A plumber has been dispatched to hostel block A "
                        "to inspect the water supply line. Expected fix "
                        "within 24 hours."
                    ),
                },
                headers={"Authorization": f"Bearer {authority_token}"},
                timeout=10,
            )
            print_response(
                "POST",
                f"/authorities/complaints/"
                f"{target_complaint}/post-update",
                r,
                label="Post authority update on Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Post authority update",
                "status_code": "ERROR",
            })

        # Change to "Resolved"
        try:
            r = requests.put(
                f"{BASE}/authorities/complaints/"
                f"{target_complaint}/status",
                json={
                    "status": "Resolved",
                    "reason": (
                        "Water supply has been restored after pipe repair."
                    ),
                },
                headers={"Authorization": f"Bearer {authority_token}"},
                timeout=10,
            )
            print_response(
                "PUT",
                f"/authorities/complaints/{target_complaint}/status",
                r,
                label="Change Complaint 1 status to 'Resolved'",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Status -> Resolved",
                "status_code": "ERROR",
            })

        # View status history
        token_viewer = student_tokens.get("23CS001") or authority_token
        try:
            r = requests.get(
                f"{BASE}/complaints/"
                f"{target_complaint}/status-history",
                headers={"Authorization": f"Bearer {token_viewer}"},
                timeout=10,
            )
            print_response(
                "GET",
                f"/complaints/{target_complaint}/status-history",
                r,
                label="Status History for Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Status History",
                "status_code": "ERROR",
            })

        # View timeline
        try:
            r = requests.get(
                f"{BASE}/complaints/{target_complaint}/timeline",
                headers={"Authorization": f"Bearer {token_viewer}"},
                timeout=10,
            )
            print_response(
                "GET",
                f"/complaints/{target_complaint}/timeline",
                r,
                label="Complaint 1 Timeline",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Complaint Timeline",
                "status_code": "ERROR",
            })
    else:
        print(
            "  SKIPPED - No authority token or Complaint 1 not available."
        )

    # ==================================================================
    # (k) STUDENT NOTIFICATIONS
    # ==================================================================
    print_header("k. STUDENT NOTIFICATIONS")

    token_s1 = student_tokens.get("23CS001")
    if token_s1:
        # Unread count
        try:
            r = requests.get(
                f"{BASE}/students/notifications/unread-count",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/students/notifications/unread-count",
                r,
                label="Unread notification count for Student 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Unread count",
                "status_code": "ERROR",
            })

        # Get notifications
        try:
            r = requests.get(
                f"{BASE}/students/notifications",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/students/notifications",
                r,
                label="Notifications for Student 1",
            )
            if (
                body
                and "notifications" in body
                and len(body["notifications"]) > 0
            ):
                notification_ids = [
                    n["id"] for n in body["notifications"]
                ]
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Get notifications",
                "status_code": "ERROR",
            })

        # Mark first notification as read
        if notification_ids:
            try:
                nid = notification_ids[0]
                r = requests.put(
                    f"{BASE}/students/notifications/{nid}/read",
                    headers={"Authorization": f"Bearer {token_s1}"},
                    timeout=10,
                )
                print_response(
                    "PUT",
                    f"/students/notifications/{nid}/read",
                    r,
                    label=f"Mark notification {nid} as read",
                )
            except Exception as exc:
                print(f"  ERROR: {exc}")
                operation_log.append({
                    "operation": "Mark notification read",
                    "status_code": "ERROR",
                })

        # Re-check unread count
        try:
            r = requests.get(
                f"{BASE}/students/notifications/unread-count",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            print_response(
                "GET",
                "/students/notifications/unread-count",
                r,
                label="Unread count after marking one as read",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Re-check unread count",
                "status_code": "ERROR",
            })
    else:
        print("  SKIPPED - No token for Student 1")

    # ==================================================================
    # (l) MY COMPLAINTS
    # ==================================================================
    print_header("l. MY COMPLAINTS")

    token_s1 = student_tokens.get("23CS001")
    if token_s1:
        try:
            r = requests.get(
                f"{BASE}/students/my-complaints",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            body = print_response(
                "GET",
                "/students/my-complaints",
                r,
                label="Student 1 (23CS001) - My Complaints",
            )
            if body and "complaints" in body:
                print(
                    f"\n  Total complaints by Student 1: "
                    f"{body.get('total', 'N/A')}"
                )
                for c in body["complaints"]:
                    print(
                        f"  - {str(c.get('id', ''))[:8]}... | "
                        f"Status: {c.get('status')} | "
                        f"Priority: {c.get('priority')} | "
                        f"Visibility: {c.get('visibility')}"
                    )
                print()
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "My Complaints",
                "status_code": "ERROR",
            })
    else:
        print("  SKIPPED - No token for Student 1")

    # ==================================================================
    # (m) COMPLAINT DETAILS
    # ==================================================================
    print_header("m. COMPLAINT DETAILS")

    target_complaint = (
        complaint_ids[0] if len(complaint_ids) > 0 else None
    )
    token_s1 = student_tokens.get("23CS001")

    if target_complaint and token_s1:
        try:
            r = requests.get(
                f"{BASE}/complaints/{target_complaint}",
                headers={"Authorization": f"Bearer {token_s1}"},
                timeout=10,
            )
            print_response(
                "GET",
                f"/complaints/{target_complaint}",
                r,
                label="Full details for Complaint 1",
            )
        except Exception as exc:
            print(f"  ERROR: {exc}")
            operation_log.append({
                "operation": "Complaint Details",
                "status_code": "ERROR",
            })
    else:
        print("  SKIPPED - Complaint 1 not available or no token.")

    # ==================================================================
    # SUMMARY
    # ==================================================================
    print(f"\n{SEPARATOR}")
    print("=== TEST RUN SUMMARY ===")
    print(THIN_SEP)
    print(f"{'#':<5} {'Operation':<60} {'Status Code':<12}")
    print(THIN_SEP)
    for i, entry in enumerate(operation_log, start=1):
        print(
            f"{i:<5} {entry['operation']:<60} "
            f"{entry['status_code']:<12}"
        )
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
    print(f"\nFinished at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
    print(SEPARATOR)


if __name__ == "__main__":
    main()
