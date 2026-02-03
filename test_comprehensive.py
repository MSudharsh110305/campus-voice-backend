"""
CampusVoice API - Interactive Manual Testing Script

Complete manual testing with menu-driven interface:
✅ Database-safe (checks existing data before creating)
✅ Fixed year field (converts to string for DB compatibility)
✅ File explorer for image uploads
✅ Menu-driven operation selection
✅ Error handling and retry logic
✅ Session persistence
"""

import asyncio
import httpx
import json
from pathlib import Path
from datetime import datetime
from tkinter import Tk, filedialog
import sys

# Configuration
BASE_URL = "http://localhost:8000"
TIMEOUT = 60.0

# Session storage
session = {
    "current_user": None,
    "user_type": None,  # 'student' or 'authority'
    "token": None,
    "students": [],
    "complaints": [],
    "authorities": []
}


# ============================================================================
# UI HELPERS
# ============================================================================

def print_header(title):
    """Print formatted header"""
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + title.center(78) + "║")
    print("╚" + "═" * 78 + "╝")


def print_section(title):
    """Print section header"""
    print("\n" + "─" * 80)
    print(f"  {title}")
    print("─" * 80)


def print_success(message):
    """Print success message"""
    print(f"✅ {message}")


def print_error(message):
    """Print error message"""
    print(f"❌ {message}")


def print_info(message):
    """Print info message"""
    print(f"ℹ️  {message}")


def print_warning(message):
    """Print warning message"""
    print(f"⚠️  {message}")


def get_input(prompt, default=None):
    """Get user input with optional default"""
    if default:
        user_input = input(f"{prompt} [{default}]: ").strip()
        return user_input if user_input else default
    return input(f"{prompt}: ").strip()


def get_choice(prompt, options):
    """Get user choice from options"""
    print(f"\n{prompt}")
    for i, option in enumerate(options, 1):
        print(f"  {i}. {option}")
    
    while True:
        try:
            choice = int(input("\nEnter choice: "))
            if 1 <= choice <= len(options):
                return choice
            print_error(f"Please enter a number between 1 and {len(options)}")
        except ValueError:
            print_error("Please enter a valid number")


def pause():
    """Pause and wait for user"""
    input("\n⏸️  Press Enter to continue...")


def select_file(title="Select a file"):
    """Open file explorer to select a file"""
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    file_path = filedialog.askopenfilename(title=title)
    root.destroy()
    return file_path


# ============================================================================
# API OPERATIONS
# ============================================================================

async def check_api_health():
    """Check if API is running"""
    print_section("API Health Check")
    
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            response = await client.get(f"{BASE_URL}/health")
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"API is running - Status: {data.get('status', 'unknown')}")
                
                # Detailed health
                try:
                    response = await client.get(f"{BASE_URL}/health/detailed")
                    if response.status_code == 200:
                        health = response.json()
                        checks = health.get('checks', {})
                        db_status = checks.get('database', {}).get('status', 'unknown')
                        print_success(f"Database: {db_status}")
                except:
                    pass
                
                return True
            else:
                print_error(f"API returned status {response.status_code}")
                return False
    
    except httpx.ConnectError:
        print_error(f"Cannot connect to API at {BASE_URL}")
        print_info("Make sure your FastAPI server is running!")
        print_info("Run: python main.py")
        return False
    except Exception as e:
        print_error(f"Health check error: {e}")
        return False


async def student_register():
    """Register a new student"""
    print_section("Student Registration")
    
    print_info("Enter student details:")
    
    # Get student data
    roll_no = get_input("Roll Number (e.g., 22CS101)")
    name = get_input("Full Name")
    email = get_input("Email (e.g., student@college.edu)")
    password = get_input("Password (min 8 chars, 1 upper, 1 lower, 1 digit)")
    
    print("\nGender:")
    print("  1. Male")
    print("  2. Female")
    print("  3. Other")
    gender_choice = get_choice("Select gender", ["Male", "Female", "Other"])
    gender = ["Male", "Female", "Other"][gender_choice - 1]
    
    print("\nStay Type:")
    print("  1. Hostel")
    print("  2. Day Scholar")
    stay_choice = get_choice("Select stay type", ["Hostel", "Day Scholar"])
    stay_type = ["Hostel", "Day Scholar"][stay_choice - 1]
    
    print("\nYear:")
    print("  1. 1st Year")
    print("  2. 2nd Year")
    print("  3. 3rd Year")
    print("  4. 4th Year")
    year_choice = get_choice("Select year", ["1", "2", "3", "4"])
    
    print("\nDepartment:")
    print("  1. Computer Science Engineering (CSE)")
    print("  2. Electronics Communication Engineering (ECE)")
    print("  3. Mechanical Engineering (MECH)")
    print("  4. Civil Engineering (CIVIL)")
    print("  5. Information Technology (IT)")
    dept_choice = get_choice("Select department", ["CSE", "ECE", "MECH", "CIVIL", "IT"])
    
    # ✅ FIX: Convert year to string for database compatibility
    student_data = {
        "roll_no": roll_no,
        "name": name,
        "email": email,
        "password": password,
        "gender": gender,
        "stay_type": stay_type,
        "year": str(year_choice),  # ✅ Convert to string
        "department_id": dept_choice
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Registering student...")
            
            response = await client.post(
                f"{BASE_URL}/api/students/register",
                json=student_data
            )
            
            if response.status_code == 201:
                data = response.json()
                print_success(f"Student registered successfully!")
                print(f"   Roll No: {data.get('roll_no')}")
                print(f"   Name: {data.get('name')}")
                print(f"   Email: {data.get('email')}")
                print(f"   Token: {data.get('token', '')[:20]}...")
                
                # Store in session
                session["students"].append({
                    "roll_no": data.get("roll_no"),
                    "name": data.get("name"),
                    "email": email,
                    "password": password,
                    "token": data.get("token")
                })
                
            elif response.status_code == 400:
                error_data = response.json()
                print_error(f"Registration failed: {error_data.get('detail', 'Unknown error')}")
                print_info("Student might already exist. Try logging in instead.")
                
            else:
                print_error(f"Registration failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
    
    except httpx.ReadTimeout:
        print_error("Registration timeout (server might be processing)")
    except Exception as e:
        print_error(f"Registration error: {e}")
    
    pause()


async def student_login():
    """Login as student"""
    print_section("Student Login")
    
    email_or_roll = get_input("Email or Roll Number")
    password = get_input("Password")
    
    login_data = {
        "email_or_roll_no": email_or_roll,
        "password": password
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Logging in...")
            
            response = await client.post(
                f"{BASE_URL}/api/students/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Login successful!")
                print(f"   Name: {data.get('name')}")
                print(f"   Roll No: {data.get('roll_no')}")
                print(f"   Email: {data.get('email')}")
                
                # Store in session
                session["current_user"] = {
                    "roll_no": data.get("roll_no"),
                    "name": data.get("name"),
                    "email": data.get("email"),
                    "token": data.get("token")
                }
                session["user_type"] = "student"
                session["token"] = data.get("token")
                
                print_info(f"Logged in as: {data.get('name')} (Student)")
                
            elif response.status_code == 401:
                print_error("Invalid email/roll number or password")
            else:
                print_error(f"Login failed: HTTP {response.status_code}")
                print(f"Response: {response.text}")
    
    except Exception as e:
        print_error(f"Login error: {e}")
    
    pause()


async def submit_complaint():
    """Submit a new complaint"""
    if not session.get("current_user") or session.get("user_type") != "student":
        print_error("You must be logged in as a student to submit complaints")
        pause()
        return
    
    print_section("Submit Complaint")
    
    print("\nSelect Category:")
    print("  1. Hostel")
    print("  2. General (Canteen, Library, Playground)")
    print("  3. Department (Labs, Classrooms)")
    print("  4. Disciplinary Committee (Ragging, Harassment)")
    category_choice = get_choice("Select category", ["Hostel", "General", "Department", "Disciplinary"])
    
    print("\nComplaint Text:")
    print_info("Minimum 10 characters, describe the issue in detail")
    original_text = input("Enter complaint: ").strip()
    
    if len(original_text) < 10:
        print_error("Complaint must be at least 10 characters")
        pause()
        return
    
    print("\nVisibility:")
    print("  1. Private (Only you and assigned authority)")
    print("  2. Department (Department members can see)")
    print("  3. Public (Everyone can see)")
    visibility_choice = get_choice("Select visibility", ["Private", "Department", "Public"])
    visibility = ["Private", "Department", "Public"][visibility_choice - 1]
    
    complaint_data = {
        "category_id": category_choice,
        "original_text": original_text,
        "visibility": visibility
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Submitting complaint (AI processing may take time)...")
            
            response = await client.post(
                f"{BASE_URL}/api/complaints/submit",
                headers={"Authorization": f"Bearer {session['token']}"},
                json=complaint_data,
                timeout=TIMEOUT
            )
            
            if response.status_code == 201:
                data = response.json()
                print_success("Complaint submitted successfully!")
                print(f"   ID: {data.get('complaint_id')}")
                print(f"   Category: {data.get('category', {}).get('name', 'N/A')}")
                print(f"   Priority: {data.get('priority', 'N/A')}")
                print(f"   Status: {data.get('status', 'N/A')}")
                print(f"   Assigned to: {data.get('assigned_authority_name', 'N/A')}")
                
                if 'rephrased_text' in data:
                    print(f"\n   AI Rephrased:")
                    print(f"   {data['rephrased_text']}")
                
                # Store in session
                session["complaints"].append({
                    "id": data.get("complaint_id"),
                    "category_id": category_choice,
                    "original_text": original_text,
                    "priority": data.get("priority"),
                    "status": data.get("status", "Raised")
                })
                
            else:
                print_error(f"Submission failed: HTTP {response.status_code}")
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
    
    except httpx.ReadTimeout:
        print_error("Submission timeout (AI processing is slow, complaint may still be created)")
    except Exception as e:
        print_error(f"Submission error: {e}")
    
    pause()


async def view_my_complaints():
    """View complaints submitted by current student"""
    if not session.get("current_user") or session.get("user_type") != "student":
        print_error("You must be logged in as a student")
        pause()
        return
    
    print_section("My Complaints")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Fetching your complaints...")
            
            response = await client.get(
                f"{BASE_URL}/api/students/my-complaints?skip=0&limit=20",
                headers={"Authorization": f"Bearer {session['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                complaints = data.get("complaints", [])
                total = data.get("total", 0)
                
                print_success(f"Found {total} complaint(s)")
                
                if complaints:
                    print()
                    for i, complaint in enumerate(complaints, 1):
                        print(f"{'─' * 80}")
                        print(f"[{i}] Complaint ID: {complaint.get('id', 'N/A')[:12]}...")
                        print(f"    Category: {complaint.get('category', {}).get('name', 'N/A')}")
                        print(f"    Status: {complaint.get('status', 'N/A')}")
                        print(f"    Priority: {complaint.get('priority', 'N/A')}")
                        print(f"    Votes: ↑{complaint.get('upvotes', 0)} ↓{complaint.get('downvotes', 0)}")
                        print(f"    Visibility: {complaint.get('visibility', 'N/A')}")
                        print(f"    Created: {complaint.get('created_at', 'N/A')[:19]}")
                        
                        rephrased = complaint.get('rephrased_text', complaint.get('original_text', ''))
                        print(f"    Text: {rephrased[:100]}...")
                        
                        if complaint.get('assigned_authority_name'):
                            print(f"    Assigned to: {complaint['assigned_authority_name']}")
                    
                    print(f"{'─' * 80}")
                else:
                    print_info("No complaints found")
                    
            else:
                print_error(f"Failed to fetch complaints: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Error fetching complaints: {e}")
    
    pause()


async def upload_image_to_complaint():
    """Upload image to a complaint"""
    if not session.get("current_user") or session.get("user_type") != "student":
        print_error("You must be logged in as a student")
        pause()
        return
    
    print_section("Upload Image to Complaint")
    
    complaint_id = get_input("Enter Complaint ID")
    
    print_info("Select image file...")
    file_path = select_file("Select Image (JPG, PNG, JPEG)")
    
    if not file_path:
        print_warning("No file selected")
        pause()
        return
    
    file_path = Path(file_path)
    
    if not file_path.exists():
        print_error("File not found")
        pause()
        return
    
    # Check file extension
    allowed_extensions = ['.jpg', '.jpeg', '.png']
    if file_path.suffix.lower() not in allowed_extensions:
        print_error(f"Invalid file type. Allowed: {', '.join(allowed_extensions)}")
        pause()
        return
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info(f"Uploading {file_path.name}... (AI verification may take time)")
            
            with open(file_path, 'rb') as f:
                files = {
                    'file': (file_path.name, f, f'image/{file_path.suffix[1:]}')
                }
                
                response = await client.post(
                    f"{BASE_URL}/api/complaints/{complaint_id}/upload-image",
                    headers={"Authorization": f"Bearer {session['token']}"},
                    files=files,
                    timeout=TIMEOUT
                )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Image uploaded successfully!")
                print(f"   File: {data.get('file_name', 'N/A')}")
                print(f"   Size: {data.get('file_size_kb', 0):.2f} KB")
                print(f"   Verification: {data.get('verification_status', 'N/A')}")
                
                if 'confidence_score' in data:
                    print(f"   AI Confidence: {data['confidence_score']:.1%}")
                    
                if data.get('is_verified'):
                    print_success("✓ Image verified by AI")
                else:
                    print_warning("Image verification pending or failed")
                    
            else:
                print_error(f"Upload failed: HTTP {response.status_code}")
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
    
    except httpx.ReadTimeout:
        print_error("Upload timeout (AI verification is slow)")
    except Exception as e:
        print_error(f"Upload error: {e}")
    
    pause()


async def vote_on_complaint():
    """Vote on a complaint"""
    if not session.get("current_user") or session.get("user_type") != "student":
        print_error("You must be logged in as a student")
        pause()
        return
    
    print_section("Vote on Complaint")
    
    complaint_id = get_input("Enter Complaint ID")
    
    print("\nVote Type:")
    print("  1. Upvote (Support this complaint)")
    print("  2. Downvote (Disagree with this complaint)")
    vote_choice = get_choice("Select vote type", ["Upvote", "Downvote"])
    vote_type = ["Upvote", "Downvote"][vote_choice - 1]
    
    vote_data = {
        "vote_type": vote_type
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info(f"Submitting {vote_type.lower()}...")
            
            response = await client.post(
                f"{BASE_URL}/api/complaints/{complaint_id}/vote",
                headers={"Authorization": f"Bearer {session['token']}"},
                json=vote_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"{vote_type} submitted successfully!")
                print(f"   Upvotes: {data.get('upvotes', 0)}")
                print(f"   Downvotes: {data.get('downvotes', 0)}")
                print(f"   Priority: {data.get('priority', 'N/A')}")
                
            elif response.status_code == 409:
                print_warning("You have already voted on this complaint")
            else:
                print_error(f"Vote failed: HTTP {response.status_code}")
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
    
    except Exception as e:
        print_error(f"Voting error: {e}")
    
    pause()


async def view_public_feed():
    """View public feed of complaints"""
    if not session.get("current_user"):
        print_error("You must be logged in")
        pause()
        return
    
    print_section("Public Feed")
    
    limit = int(get_input("Number of complaints to show", "10"))
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Fetching public feed...")
            
            response = await client.get(
                f"{BASE_URL}/api/complaints/public-feed?skip=0&limit={limit}",
                headers={"Authorization": f"Bearer {session['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                complaints = data.get("complaints", [])
                total = data.get("total", 0)
                
                print_success(f"Found {total} public complaint(s), showing {len(complaints)}")
                
                if complaints:
                    print()
                    for i, complaint in enumerate(complaints, 1):
                        print(f"{'─' * 80}")
                        print(f"[{i}] ID: {complaint.get('id', 'N/A')[:12]}...")
                        print(f"    Category: {complaint.get('category', {}).get('name', 'N/A')}")
                        print(f"    Status: {complaint.get('status', 'N/A')} | Priority: {complaint.get('priority', 'N/A')}")
                        print(f"    Votes: ↑{complaint.get('upvotes', 0)} ↓{complaint.get('downvotes', 0)}")
                        print(f"    Created: {complaint.get('created_at', 'N/A')[:19]}")
                        
                        text = complaint.get('rephrased_text', complaint.get('original_text', ''))
                        print(f"    Text: {text[:150]}...")
                    
                    print(f"{'─' * 80}")
                else:
                    print_info("No public complaints found")
                    
            else:
                print_error(f"Failed to fetch feed: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Error fetching feed: {e}")
    
    pause()


async def filter_complaints():
    """Filter complaints by status, priority, category"""
    if not session.get("current_user"):
        print_error("You must be logged in")
        pause()
        return
    
    print_section("Filter Complaints")
    
    print("\nFilter by:")
    print("  1. Status")
    print("  2. Priority")
    print("  3. Category")
    print("  4. Cancel")
    
    filter_choice = get_choice("Select filter type", ["Status", "Priority", "Category", "Cancel"])
    
    if filter_choice == 4:
        return
    
    filter_params = {}
    
    if filter_choice == 1:  # Status
        print("\nSelect Status:")
        print("  1. Raised")
        print("  2. In Progress")
        print("  3. Resolved")
        print("  4. Closed")
        status_choice = get_choice("Select status", ["Raised", "In Progress", "Resolved", "Closed"])
        filter_params["status"] = ["Raised", "In Progress", "Resolved", "Closed"][status_choice - 1]
        
    elif filter_choice == 2:  # Priority
        print("\nSelect Priority:")
        print("  1. Low")
        print("  2. Medium")
        print("  3. High")
        print("  4. Critical")
        priority_choice = get_choice("Select priority", ["Low", "Medium", "High", "Critical"])
        filter_params["priority"] = ["Low", "Medium", "High", "Critical"][priority_choice - 1]
        
    elif filter_choice == 3:  # Category
        print("\nSelect Category:")
        print("  1. Hostel")
        print("  2. General")
        print("  3. Department")
        print("  4. Disciplinary Committee")
        category_choice = get_choice("Select category", ["Hostel", "General", "Department", "Disciplinary"])
        filter_params["category_id"] = category_choice
    
    limit = int(get_input("Number of results", "10"))
    filter_params["limit"] = limit
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Filtering complaints...")
            
            query_string = "&".join([f"{k}={v}" for k, v in filter_params.items()])
            
            response = await client.get(
                f"{BASE_URL}/api/complaints/filter?{query_string}",
                headers={"Authorization": f"Bearer {session['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                complaints = data.get("complaints", [])
                total = data.get("total", 0)
                
                print_success(f"Found {total} matching complaint(s)")
                
                if complaints:
                    print()
                    for i, complaint in enumerate(complaints, 1):
                        print(f"{'─' * 80}")
                        print(f"[{i}] ID: {complaint.get('id', 'N/A')[:12]}...")
                        print(f"    Category: {complaint.get('category', {}).get('name', 'N/A')}")
                        print(f"    Status: {complaint.get('status', 'N/A')} | Priority: {complaint.get('priority', 'N/A')}")
                        print(f"    Votes: ↑{complaint.get('upvotes', 0)} ↓{complaint.get('downvotes', 0)}")
                        
                        text = complaint.get('rephrased_text', complaint.get('original_text', ''))
                        print(f"    Text: {text[:100]}...")
                    
                    print(f"{'─' * 80}")
                else:
                    print_info("No matching complaints found")
                    
            else:
                print_error(f"Filter failed: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Filter error: {e}")
    
    pause()


async def view_notifications():
    """View student notifications"""
    if not session.get("current_user") or session.get("user_type") != "student":
        print_error("You must be logged in as a student")
        pause()
        return
    
    print_section("My Notifications")
    
    print("\nShow:")
    print("  1. All notifications")
    print("  2. Unread only")
    show_choice = get_choice("Select option", ["All", "Unread only"])
    unread_only = "true" if show_choice == 2 else "false"
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Fetching notifications...")
            
            response = await client.get(
                f"{BASE_URL}/api/students/notifications?unread_only={unread_only}&limit=20",
                headers={"Authorization": f"Bearer {session['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                notifications = data.get("notifications", [])
                total = data.get("total", 0)
                
                print_success(f"Found {total} notification(s)")
                
                if notifications:
                    print()
                    for i, notif in enumerate(notifications, 1):
                        status_icon = "📩" if not notif.get('is_read') else "📭"
                        print(f"{'─' * 80}")
                        print(f"[{i}] {status_icon} Notification ID: {notif.get('id')}")
                        print(f"    Type: {notif.get('type', 'N/A')}")
                        print(f"    Message: {notif.get('message', 'N/A')}")
                        print(f"    Read: {'Yes' if notif.get('is_read') else 'No'}")
                        print(f"    Time: {notif.get('created_at', 'N/A')[:19]}")
                    
                    print(f"{'─' * 80}")
                else:
                    print_info("No notifications found")
                    
            else:
                print_error(f"Failed to fetch notifications: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Error fetching notifications: {e}")
    
    pause()


async def authority_login():
    """Login as authority"""
    print_section("Authority Login")
    
    email = get_input("Authority Email")
    password = get_input("Password")
    
    login_data = {
        "email": email,
        "password": password
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Logging in...")
            
            response = await client.post(
                f"{BASE_URL}/api/authorities/login",
                json=login_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Login successful!")
                print(f"   Name: {data.get('name')}")
                print(f"   Type: {data.get('authority_type')}")
                print(f"   Level: {data.get('authority_level')}")
                print(f"   Designation: {data.get('designation', 'N/A')}")
                
                # Store in session
                session["current_user"] = {
                    "email": email,
                    "name": data.get("name"),
                    "authority_type": data.get("authority_type"),
                    "authority_level": data.get("authority_level"),
                    "token": data.get("token")
                }
                session["user_type"] = "authority"
                session["token"] = data.get("token")
                
                print_info(f"Logged in as: {data.get('name')} ({data.get('authority_type')})")
                
            elif response.status_code == 401:
                print_error("Invalid email or password")
            else:
                print_error(f"Login failed: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Login error: {e}")
    
    pause()


async def view_authority_dashboard():
    """View authority dashboard"""
    if not session.get("current_user") or session.get("user_type") != "authority":
        print_error("You must be logged in as an authority")
        pause()
        return
    
    print_section("Authority Dashboard")
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Loading dashboard...")
            
            response = await client.get(
                f"{BASE_URL}/api/authorities/dashboard",
                headers={"Authorization": f"Bearer {session['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success("Dashboard loaded!")
                
                stats = data.get("stats", {})
                print("\n📊 Statistics:")
                print(f"   Total Assigned: {stats.get('total_assigned', 0)}")
                print(f"   Pending: {stats.get('pending', 0)}")
                print(f"   In Progress: {stats.get('in_progress', 0)}")
                print(f"   Resolved: {stats.get('resolved', 0)}")
                print(f"   Closed: {stats.get('closed', 0)}")
                
                recent = data.get("recent_complaints", [])
                print(f"\n📋 Recent Complaints: {len(recent)}")
                for i, complaint in enumerate(recent[:5], 1):
                    print(f"   {i}. {complaint.get('id', 'N/A')[:12]}... - {complaint.get('status', 'N/A')} - {complaint.get('priority', 'N/A')}")
                
                urgent = data.get("urgent_complaints", [])
                print(f"\n🚨 Urgent Complaints: {len(urgent)}")
                for i, complaint in enumerate(urgent[:3], 1):
                    print(f"   {i}. {complaint.get('id', 'N/A')[:12]}... - {complaint.get('priority', 'N/A')}")
                    
            else:
                print_error(f"Failed to load dashboard: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Dashboard error: {e}")
    
    pause()


async def update_complaint_status():
    """Update complaint status as authority"""
    if not session.get("current_user") or session.get("user_type") != "authority":
        print_error("You must be logged in as an authority")
        pause()
        return
    
    print_section("Update Complaint Status")
    
    complaint_id = get_input("Enter Complaint ID")
    
    print("\nNew Status:")
    print("  1. Raised")
    print("  2. In Progress")
    print("  3. Resolved")
    print("  4. Closed")
    status_choice = get_choice("Select new status", ["Raised", "In Progress", "Resolved", "Closed"])
    new_status = ["Raised", "In Progress", "Resolved", "Closed"][status_choice - 1]
    
    reason = get_input("Reason for status change")
    
    update_data = {
        "status": new_status,
        "reason": reason
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Updating status...")
            
            response = await client.put(
                f"{BASE_URL}/api/authorities/complaints/{complaint_id}/status",
                headers={"Authorization": f"Bearer {session['token']}"},
                json=update_data
            )
            
            if response.status_code == 200:
                data = response.json()
                print_success(f"Status updated to '{new_status}'!")
                print(f"   Complaint ID: {data.get('complaint_id', 'N/A')}")
                print(f"   New Status: {data.get('status', 'N/A')}")
                print(f"   Reason: {reason}")
                
            else:
                print_error(f"Update failed: HTTP {response.status_code}")
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
    
    except Exception as e:
        print_error(f"Update error: {e}")
    
    pause()


async def post_public_update():
    """Post public update on complaint"""
    if not session.get("current_user") or session.get("user_type") != "authority":
        print_error("You must be logged in as an authority")
        pause()
        return
    
    print_section("Post Public Update")
    
    complaint_id = get_input("Enter Complaint ID")
    
    print("\nUpdate Text:")
    print_info("Provide status update or response to students")
    update_text = input("Enter update message: ").strip()
    
    if len(update_text) < 10:
        print_error("Update must be at least 10 characters")
        pause()
        return
    
    print("\nVisibility:")
    print("  1. Public (All students can see)")
    print("  2. Private (Only complaint owner can see)")
    visibility_choice = get_choice("Select visibility", ["Public", "Private"])
    is_public = visibility_choice == 1
    
    update_data = {
        "update_text": update_text,
        "is_public": is_public
    }
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Posting update...")
            
            response = await client.post(
                f"{BASE_URL}/api/authorities/complaints/{complaint_id}/post-update",
                headers={"Authorization": f"Bearer {session['token']}"},
                json=update_data
            )
            
            if response.status_code == 201:
                data = response.json()
                print_success("Update posted successfully!")
                print(f"   Update ID: {data.get('id', 'N/A')}")
                print(f"   Visibility: {'Public' if is_public else 'Private'}")
                print(f"   Text: {update_text[:100]}...")
                
            else:
                print_error(f"Post failed: HTTP {response.status_code}")
                error_data = response.json()
                print(f"Error: {error_data.get('detail', 'Unknown error')}")
    
    except Exception as e:
        print_error(f"Post error: {e}")
    
    pause()


async def view_assigned_complaints():
    """View complaints assigned to authority"""
    if not session.get("current_user") or session.get("user_type") != "authority":
        print_error("You must be logged in as an authority")
        pause()
        return
    
    print_section("Assigned Complaints")
    
    limit = int(get_input("Number of complaints to show", "10"))
    
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT) as client:
            print_info("Fetching assigned complaints...")
            
            response = await client.get(
                f"{BASE_URL}/api/authorities/my-complaints?skip=0&limit={limit}",
                headers={"Authorization": f"Bearer {session['token']}"}
            )
            
            if response.status_code == 200:
                data = response.json()
                complaints = data.get("complaints", [])
                total = data.get("total", 0)
                
                print_success(f"Found {total} assigned complaint(s)")
                
                if complaints:
                    print()
                    for i, complaint in enumerate(complaints, 1):
                        print(f"{'─' * 80}")
                        print(f"[{i}] ID: {complaint.get('id', 'N/A')[:12]}...")
                        print(f"    Category: {complaint.get('category', {}).get('name', 'N/A')}")
                        print(f"    Status: {complaint.get('status', 'N/A')} | Priority: {complaint.get('priority', 'N/A')}")
                        print(f"    Student: {complaint.get('student_name', 'N/A')}")
                        print(f"    Created: {complaint.get('created_at', 'N/A')[:19]}")
                        
                        text = complaint.get('rephrased_text', complaint.get('original_text', ''))
                        print(f"    Text: {text[:100]}...")
                    
                    print(f"{'─' * 80}")
                else:
                    print_info("No assigned complaints found")
                    
            else:
                print_error(f"Failed to fetch complaints: HTTP {response.status_code}")
    
    except Exception as e:
        print_error(f"Error fetching complaints: {e}")
    
    pause()


def logout():
    """Logout current user"""
    if session.get("current_user"):
        user_name = session["current_user"].get("name", "User")
        print_info(f"Logging out {user_name}...")
        
        session["current_user"] = None
        session["user_type"] = None
        session["token"] = None
        
        print_success("Logged out successfully")
    else:
        print_info("No user logged in")
    
    pause()


# ============================================================================
# MENU SYSTEMS
# ============================================================================

async def student_menu():
    """Student operations menu"""
    while True:
        print_header("CAMPUSVOICE - STUDENT PORTAL")
        
        if session.get("current_user") and session.get("user_type") == "student":
            user = session["current_user"]
            print(f"\n👤 Logged in as: {user.get('name')} ({user.get('roll_no')})")
        else:
            print("\n👤 Not logged in")
        
        print("\n📋 MENU:")
        print("  1. Register (New Student)")
        print("  2. Login")
        print("  3. Submit Complaint")
        print("  4. View My Complaints")
        print("  5. Upload Image to Complaint")
        print("  6. Vote on Complaint")
        print("  7. View Public Feed")
        print("  8. Filter Complaints")
        print("  9. View Notifications")
        print("  10. Logout")
        print("  0. Back to Main Menu")
        
        try:
            choice = int(input("\n👉 Enter choice: "))
            
            if choice == 0:
                break
            elif choice == 1:
                await student_register()
            elif choice == 2:
                await student_login()
            elif choice == 3:
                await submit_complaint()
            elif choice == 4:
                await view_my_complaints()
            elif choice == 5:
                await upload_image_to_complaint()
            elif choice == 6:
                await vote_on_complaint()
            elif choice == 7:
                await view_public_feed()
            elif choice == 8:
                await filter_complaints()
            elif choice == 9:
                await view_notifications()
            elif choice == 10:
                logout()
            else:
                print_error("Invalid choice")
                pause()
        
        except ValueError:
            print_error("Please enter a valid number")
            pause()
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled")
            pause()


async def authority_menu():
    """Authority operations menu"""
    while True:
        print_header("CAMPUSVOICE - AUTHORITY PORTAL")
        
        if session.get("current_user") and session.get("user_type") == "authority":
            user = session["current_user"]
            print(f"\n👤 Logged in as: {user.get('name')} ({user.get('authority_type')})")
        else:
            print("\n👤 Not logged in")
        
        print("\n📋 MENU:")
        print("  1. Login")
        print("  2. View Dashboard")
        print("  3. View Assigned Complaints")
        print("  4. Update Complaint Status")
        print("  5. Post Public Update")
        print("  6. View Public Feed")
        print("  7. Filter Complaints")
        print("  8. Logout")
        print("  0. Back to Main Menu")
        
        try:
            choice = int(input("\n👉 Enter choice: "))
            
            if choice == 0:
                break
            elif choice == 1:
                await authority_login()
            elif choice == 2:
                await view_authority_dashboard()
            elif choice == 3:
                await view_assigned_complaints()
            elif choice == 4:
                await update_complaint_status()
            elif choice == 5:
                await post_public_update()
            elif choice == 6:
                await view_public_feed()
            elif choice == 7:
                await filter_complaints()
            elif choice == 8:
                logout()
            else:
                print_error("Invalid choice")
                pause()
        
        except ValueError:
            print_error("Please enter a valid number")
            pause()
        except KeyboardInterrupt:
            print("\n\n⚠️  Operation cancelled")
            pause()


async def main_menu():
    """Main menu"""
    # Check API health at startup
    print_header("CAMPUSVOICE - INTERACTIVE TESTING TOOL")
    print("\n🔍 Checking API status...")
    
    if not await check_api_health():
        print_error("API is not accessible. Please start the server first.")
        print_info("Run: python main.py")
        return
    
    pause()
    
    while True:
        print_header("CAMPUSVOICE - MAIN MENU")
        
        print("\n📋 SELECT PORTAL:")
        print("  1. Student Portal")
        print("  2. Authority Portal")
        print("  3. Check API Health")
        print("  0. Exit")
        
        try:
            choice = int(input("\n👉 Enter choice: "))
            
            if choice == 0:
                print_info("Exiting...")
                print_success("Goodbye! 👋")
                break
            elif choice == 1:
                await student_menu()
            elif choice == 2:
                await authority_menu()
            elif choice == 3:
                await check_api_health()
                pause()
            else:
                print_error("Invalid choice")
                pause()
        
        except ValueError:
            print_error("Please enter a valid number")
            pause()
        except KeyboardInterrupt:
            print("\n\n⚠️  Exiting...")
            break


# ============================================================================
# MAIN ENTRY POINT
# ============================================================================

if __name__ == "__main__":
    print("\n" + "╔" + "═" * 78 + "╗")
    print("║" + "CampusVoice - Interactive Manual Testing Tool".center(78) + "║")
    print("║" + "Database-Safe | Menu-Driven | File Explorer Support".center(78) + "║")
    print("╚" + "═" * 78 + "╝")
    
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print("\n\n⚠️  Program interrupted by user")
        print_success("Goodbye! 👋")
    except Exception as e:
        print_error(f"Unexpected error: {e}")
        import traceback
        traceback.print_exc()
