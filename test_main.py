"""
Lightweight in-memory FastAPI app + test harness to exercise core CampusVoice flows:
- Student register / login
- Submit complaint (AI-like categorization & assignment using keywords)
- View my complaints
- Public feed (filters: stay_type, department)
- Vote on complaints
- Upload image to complaint (uses src.utils.file_upload.FileUploadHandler)
- Authority login / view assigned / update status

Run: python test_main.py
"""

from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Header
from fastapi.responses import JSONResponse
import uvicorn
import asyncio
import httpx
import uuid
from typing import Optional, List, Dict, Any
from datetime import datetime, timezone
import json

# Reuse existing utilities
from src.utils.validators import (
    validate_email,
    validate_roll_no,
    validate_complaint_text,
    validate_file_extension,
    validate_visibility,
)
from src.utils.helpers import generate_random_string, get_time_ago, is_valid_uuid
from src.utils.file_upload import file_upload_handler
from src.config.constants import (
    CATEGORIES,
    DEFAULT_CATEGORY_ROUTING,
    AUTHORITY_LEVELS,
    VALID_YEARS,
    VisibilityLevel,
    VoteType,
    SPAM_KEYWORDS,
    MIN_COMPLAINT_LENGTH,
)

app = FastAPI(title="CampusVoice Test API (in-memory)")

# In-memory stores for testing
STUDENTS: Dict[str, Dict] = {}        # key: email or roll_no
TOKENS: Dict[str, Dict] = {}         # token -> {"role": "student"/"authority", "id": ...}
COMPLAINTS: Dict[str, Dict] = {}     # id -> complaint dict
VOTES: Dict[str, Dict[str, str]] = {}  # complaint_id -> {token: vote_type}
AUTHORITIES: Dict[str, Dict] = {}    # email -> authority dict (simple)

# Simple helpers
def require_token(auth: Optional[str] = Header(None)):
    if not auth:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not auth.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization header")
    token = auth.split(" ", 1)[1].strip()
    session = TOKENS.get(token)
    if not session:
        raise HTTPException(status_code=401, detail="Invalid or expired token")
    return token

def get_session_user(token: str):
    return TOKENS.get(token)

def simple_llm_categorize_and_route(text: str) -> Dict[str, Any]:
    """Heuristic LLM: choose category by keyword frequency from CATEGORIES and route to default authority."""
    text_lower = text.lower()
    scores = []
    for cat in CATEGORIES:
        kws = cat.get("keywords", [])
        score = sum(1 for kw in kws if kw in text_lower)
        scores.append((score, cat))
    scores.sort(reverse=True, key=lambda x: x[0])
    best_score, best_cat = scores[0]
    category = best_cat["name"] if best_score > 0 else "General"
    assigned_authority = DEFAULT_CATEGORY_ROUTING.get(category, "Admin Officer")
    return {"category": {"name": category}, "assigned_authority_name": assigned_authority}

# Robust optional imports for external service modules
try:
	from src.services import llm_service
except Exception:
	llm_service = None

try:
	from src.services import image_verification
except Exception:
	image_verification = None

# optional spam detection/classifier
try:
	from src.services import spam_detection
except Exception:
	spam_detection = None

def paraphrase_text(text: str) -> str:
    """
    Prefer external llm_service.rephrase_text if available, otherwise local fallback.
    """
    if llm_service is not None and hasattr(llm_service, "rephrase_text"):
        try:
            out = llm_service.rephrase_text(text)
            if out and isinstance(out, str):
                return out
        except Exception:
            # fall back to local behavior
            pass

    # Local lightweight paraphrase fallback
    try:
        words = text.split()
        if len(words) <= 3:
            return " ".join(reversed(words))
        for i in range(0, len(words) - 1, 2):
            words[i], words[i + 1] = words[i + 1], words[i]
        paraphrased = " ".join(words)
        return paraphrased if paraphrased != text else text[::-1]
    except Exception:
        return text

# -------------------------
# Auth & Student endpoints
# -------------------------
@app.post("/api/students/register")
async def student_register(payload: Dict):
    email = payload.get("email")
    roll_no = payload.get("roll_no")
    name = payload.get("name")
    password = payload.get("password")
    year = payload.get("year")
    department_id = payload.get("department_id")
    stay_type = payload.get("stay_type")
    
    ok, errmsg = validate_email(email)
    if not ok:
        raise HTTPException(status_code=400, detail=errmsg)
    ok, errmsg = validate_roll_no(roll_no)
    if not ok:
        raise HTTPException(status_code=400, detail=errmsg)
    if year not in VALID_YEARS:
        raise HTTPException(status_code=400, detail="Invalid year")
    key = email.lower()
    if key in STUDENTS:
        return JSONResponse(status_code=400, content={"detail": "Student already exists"})
    STUDENTS[key] = {
        "roll_no": roll_no,
        "name": name,
        "email": email,
        "password": password,
        "year": year,
        "department_id": department_id,
        "stay_type": stay_type,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    token = generate_random_string(32)
    TOKENS[token] = {"role": "student", "email": email}
    return JSONResponse(status_code=201, content={
        "roll_no": roll_no,
        "name": name,
        "email": email,
        "token": token
    })

@app.post("/api/students/login")
async def student_login(payload: Dict):
    email_or_roll = payload.get("email_or_roll_no")
    password = payload.get("password")
    # find by email or roll
    user = None
    for s in STUDENTS.values():
        if s["email"] == email_or_roll or s["roll_no"] == email_or_roll:
            user = s
            break
    if not user or user["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_random_string(32)
    TOKENS[token] = {"role": "student", "email": user["email"]}
    return {"name": user["name"], "roll_no": user["roll_no"], "email": user["email"], "token": token}

# -------------------------
# Complaint endpoints
# -------------------------
@app.post("/api/complaints/submit")
async def submit_complaint(payload: Dict, authorization: str = Header(None)):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can submit complaints")
    text = payload.get("original_text", "") or payload.get("text", "")
    visibility = payload.get("visibility", "Private")
    ok, err = validate_complaint_text(text)
    if not ok:
        raise HTTPException(status_code=400, detail=err)
    ok, verr = validate_visibility(visibility)
    if not ok:
        raise HTTPException(status_code=400, detail=verr)

    # Rephrase using LLM service if present
    rephrased = paraphrase_text(text)

    # Determine assigned authority role and email (unchanged logic, but keep explicit email)
    llm_res = simple_llm_categorize_and_route(text)
    assigned_role = llm_res.get("assigned_authority_name", "Admin Officer")

    assigned_email = None
    for auth_email, auth in AUTHORITIES.items():
        auth_type = auth.get("authority_type", "").lower()
        if assigned_role.lower() in auth_type:
            assigned_email = auth_email
            break
    if not assigned_email:
        assigned_email = f"{assigned_role.replace(' ', '').lower()}@college.edu"

    student_email = session["email"]
    student = STUDENTS.get(student_email.lower(), {})
    student_dept = student.get("department_id")

    complaint_id = str(uuid.uuid4())
    complaint = {
        "id": complaint_id,
        "original_text": text,
        "rephrased_text": rephrased,
        "category": llm_res["category"],
        "assigned_authority_name": assigned_role,
        "assigned_authority_email": assigned_email,
        "status": "Raised",
        "priority": "Low",
        "visibility": visibility,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "student_email": student_email,
        "student_department_id": student_dept,
        "upvotes": 0,
        "downvotes": 0,
        "has_image": False,
        "updates": [],
    }
    # Run spam/abuse detection on complaint text if available
    is_spam = False
    is_abusive = False
    try:
        if spam_detection is not None and hasattr(spam_detection, "classify_text"):
            r = spam_detection.classify_text(text)
            is_spam = bool(r.get("is_spam", False))
            is_abusive = bool(r.get("is_abusive", False))
        elif llm_service is not None and hasattr(llm_service, "classify_text"):
            r = llm_service.classify_text(text)
            is_spam = bool(r.get("is_spam", False))
            is_abusive = bool(r.get("is_abusive", False))
    except Exception:
        is_spam = False
        is_abusive = False

    if is_spam or is_abusive:
        complaint["status"] = "Spam"

    COMPLAINTS[complaint_id] = complaint
    return JSONResponse(status_code=201, content={
        "complaint_id": complaint_id,
        "category": complaint["category"],
        "assigned_authority_name": complaint["assigned_authority_name"],
        "assigned_authority_email": complaint["assigned_authority_email"],
        "rephrased_text": complaint["rephrased_text"],
        "status": complaint["status"],
        "priority": complaint["priority"]
    })

@app.get("/api/students/my-complaints")
async def my_complaints(authorization: str = Header(None), skip: int = 0, limit: int = 20):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students allowed")
    email = session["email"]
    items = [c for c in COMPLAINTS.values() if c["student_email"] == email]
    total = len(items)
    return {"complaints": items[skip:skip+limit], "total": total}

@app.get("/api/complaints/public-feed")
async def public_feed(authorization: str = Header(None), skip: int = 0, limit: int = 20, stay_type: Optional[str] = None, department: Optional[str] = None):
    token = require_token(authorization)
    session = get_session_user(token)
    requester_email = session.get("email")
    requester = STUDENTS.get(requester_email.lower()) if session.get("role") == "student" else None
    requester_dept = requester.get("department_id") if requester else None
    requester_stay = requester.get("stay_type") if requester else None

    items = []
    for c in COMPLAINTS.values():
        # enforce visibility rules
        vis = c.get("visibility", "Private")
        cat_name = c.get("category", {}).get("name", "")

        # Private -> only owner or assigned authority
        if vis == "Private":
            if requester_email != c.get("student_email") and not (session.get("role") == "authority" and session.get("email") == c.get("assigned_authority_email")):
                continue

        # Department -> only same-department students and authorities
        if vis == "Department":
            if session.get("role") == "student":
                if requester_dept is None or requester_dept != c.get("student_department_id"):
                    continue
            elif session.get("role") == "authority":
                # allow authority if assigned or same department-level authority (best-effort)
                if session.get("email") != c.get("assigned_authority_email"):
                    continue

        # Public -> apply additional rules:
        if vis == "Public":
            # hostel complaints should not be shown to day scholars
            if cat_name.lower() == "hostel" and requester and requester.get("stay_type") == "Day Scholar":
                continue
            # inter-department complaints not shown to other departments (if Department category)
            if cat_name.lower() == "department" and requester and requester_dept and c.get("student_department_id") and requester_dept != c.get("student_department_id"):
                # but if requester is the owner, allow
                if requester_email != c.get("student_email"):
                    continue

        # apply optional query filters
        if stay_type and c.get("visibility") == "Public":
            student = STUDENTS.get(c["student_email"].lower())
            if not student or student.get("stay_type") != stay_type:
                continue
        if department and c.get("visibility") == "Public":
            student = STUDENTS.get(c["student_email"].lower())
            if not student or student.get("department_id") != department:
                continue

        items.append(c)

    total = len(items)
    return {"complaints": items[skip:skip+limit], "total": total}

@app.post("/api/complaints/{complaint_id}/vote")
async def vote_complaint(complaint_id: str, payload: Dict, authorization: str = Header(None)):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can vote")
    vote_type = payload.get("vote_type")
    if vote_type not in ["Upvote", "Downvote"]:
        raise HTTPException(status_code=400, detail="Invalid vote type")
    c = COMPLAINTS.get(complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")

    # Use stable student identifier (email) for deduplication
    student_email = session.get("email")
    votes_for = VOTES.setdefault(complaint_id, {})
    if student_email in votes_for:
        raise HTTPException(status_code=409, detail="You have already voted")

    votes_for[student_email] = vote_type
    # Recompute aggregate counts from votes_for to keep consistent
    up = sum(1 for v in votes_for.values() if v == "Upvote")
    down = sum(1 for v in votes_for.values() if v == "Downvote")
    c["upvotes"] = up
    c["downvotes"] = down

    # Recalculate simple priority
    score = up * 5 + down * -3
    if score >= 200:
        c["priority"] = "Critical"
    elif score >= 100:
        c["priority"] = "High"
    elif score >= 50:
        c["priority"] = "Medium"
    else:
        c["priority"] = "Low"
    return {"upvotes": c["upvotes"], "downvotes": c["downvotes"], "priority": c["priority"]}

# -------------------------
# Image upload & verify
# -------------------------
@app.post("/api/complaints/{complaint_id}/upload-image")
async def upload_image(complaint_id: str, file: UploadFile = File(...), authorization: str = Header(None)):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "student":
        raise HTTPException(status_code=403, detail="Only students can upload images")
    c = COMPLAINTS.get(complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    # Validate extension
    ok, errmsg = validate_file_extension(file.filename, ["jpg", "jpeg", "png", "gif", "webp"])
    if not ok:
        raise HTTPException(status_code=400, detail=errmsg)
    # Read and validate bytes via file_upload_handler
    image_bytes, mimetype, size, filename = await file_upload_handler.read_image_bytes(file)

    # Default verification result
    verification = {"status": "verified", "mimetype": mimetype, "size_bytes": size, "confidence": 0.95, "notes": []}

    # 1) If image_verification service is available, use it
    if image_verification is not None and hasattr(image_verification, "verify_image"):
        try:
            result = image_verification.verify_image(image_bytes)
            # Expected result fields: is_relevant, is_spam, is_abusive, confidence
            is_relevant = bool(result.get("is_relevant", True))
            is_spam = bool(result.get("is_spam", False))
            is_abusive = bool(result.get("is_abusive", False))
            confidence = float(result.get("confidence", 0.9))
            if not is_relevant or is_spam or is_abusive:
                verification["status"] = "rejected"
                verification["notes"] = []
                if not is_relevant:
                    verification["notes"].append("not_relevant")
                if is_spam:
                    verification["notes"].append("spam")
                if is_abusive:
                    verification["notes"].append("abusive")
                verification["confidence"] = confidence
            else:
                verification["status"] = "verified"
                verification["confidence"] = confidence
        except Exception as e:
            # fallback to heuristic below
            verification["notes"] = [f"verification_error:{e}"]

    # 2) Fallback heuristic: mark rejected if complaint text contains spam keywords or if image_verification indicated spam/abusive
    if verification.get("status") != "rejected":
        text_lower = c["original_text"].lower()
        if any(k in text_lower for k in SPAM_KEYWORDS):
            verification["status"] = "rejected"
            # ensure notes is list then append
            notes = list(verification.get("notes", []))
            notes.append("spam_keyword_detected")
            verification["notes"] = notes
            verification["confidence"] = 0.1

    # Persist image metadata and verification
    c["has_image"] = True
    c["image_metadata"] = file_upload_handler.get_image_metadata(image_bytes)
    c["image_verification"] = {
        "status": verification["status"],
        "mimetype": verification["mimetype"],
        "size_bytes": verification["size_bytes"],
        "confidence": verification.get("confidence", 0.0),
        "notes": verification.get("notes", "")
    }

    # If content is abusive/spam -> mark complaint as Spam for moderation
    if c["image_verification"]["status"] == "rejected" and ("spam" in str(c["image_verification"].get("notes", "")).lower() or "abusive" in str(c["image_verification"].get("notes", "")).lower()):
        c["status"] = "Spam"

    return {
        "file_name": filename,
        "file_size_kb": size / 1024,
        "verification_status": c["image_verification"]["status"],
        "is_verified": c["image_verification"]["status"] == "verified",
        "confidence_score": c["image_verification"].get("confidence", 0.0)
    }

# -------------------------
# Authority endpoints
# -------------------------
@app.post("/api/authorities/login")
async def authority_login(payload: Dict):
    email = payload.get("email")
    password = payload.get("password")
    # allow simple creation on first login: if not present, create a sample authority
    auth = AUTHORITIES.get(email.lower())
    if not auth:
        # create a simple authority with level from AUTHORITY_LEVELS if present else 10
        auth = {
            "email": email,
            "name": payload.get("email").split("@")[0],
            "password": password,
            "authority_type": "Admin Officer",
            "authority_level": AUTHORITY_LEVELS.get("Admin Officer", 50)
        }
        AUTHORITIES[email.lower()] = auth
    if auth["password"] != password:
        raise HTTPException(status_code=401, detail="Invalid credentials")
    token = generate_random_string(32)
    TOKENS[token] = {"role": "authority", "email": email}
    return {"name": auth["name"], "authority_type": auth["authority_type"], "authority_level": auth["authority_level"], "token": token}

@app.get("/api/authorities/my-complaints")
async def authority_my_complaints(authorization: str = Header(None), skip: int = 0, limit: int = 20):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "authority":
        raise HTTPException(status_code=403, detail="Only authorities allowed")
    email = session["email"].lower()

    # find authority record to check level
    auth_record = AUTHORITIES.get(email)
    auth_level = auth_record.get("authority_level", 0) if auth_record else 0

    if auth_level >= 100:
        # admin sees all
        items = list(COMPLAINTS.values())
    else:
        # return complaints assigned explicitly to this authority email
        items = [c for c in COMPLAINTS.values() if c.get("assigned_authority_email", "").lower() == email]

    return {"complaints": items[skip:skip+limit], "total": len(items)}

@app.put("/api/authorities/complaints/{complaint_id}/status")
async def authority_update_status(complaint_id: str, payload: Dict, authorization: str = Header(None)):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "authority":
        raise HTTPException(status_code=403, detail="Only authorities can update status")
    c = COMPLAINTS.get(complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    new_status = payload.get("status")
    reason = payload.get("reason", "")
    # simple validation of transitions: allow any for test
    c["status"] = new_status
    # create simple update log
    c.setdefault("status_history", []).append({"status": new_status, "reason": reason, "updated_at": datetime.now(timezone.utc).isoformat()})
    return {"complaint_id": complaint_id, "status": new_status}

@app.post("/api/authorities/complaints/{complaint_id}/post-update")
async def authority_post_update(complaint_id: str, payload: Dict, authorization: str = Header(None)):
    token = require_token(authorization)
    session = get_session_user(token)
    if session["role"] != "authority":
        raise HTTPException(status_code=403, detail="Only authorities can post updates")
    c = COMPLAINTS.get(complaint_id)
    if not c:
        raise HTTPException(status_code=404, detail="Complaint not found")
    auth_email = session.get("email")
    auth_record = AUTHORITIES.get(auth_email)
    auth_level = auth_record.get("authority_level", 0) if auth_record else 0
    # require authority assigned to this complaint (or admin)
    if auth_level < 100 and c.get("assigned_authority_email", "").lower() != auth_email.lower():
        raise HTTPException(status_code=403, detail="Not authorized to post update for this complaint")
    update_text = payload.get("update_text", "")
    is_public = bool(payload.get("is_public", True))

    # optional: run spam/abuse check on update text via llm_service if available
    is_spam = False
    is_abusive = False
    confidence = 1.0
    if llm_service is not None and hasattr(llm_service, "classify_text"):
        try:
            cls = llm_service.classify_text(update_text)
            is_spam = bool(cls.get("is_spam", False))
            is_abusive = bool(cls.get("is_abusive", False))
            confidence = float(cls.get("confidence", 1.0))
        except Exception:
            pass
    else:
        if any(k in update_text.lower() for k in SPAM_KEYWORDS):
            is_spam = True
            confidence = 0.2

    if is_spam or is_abusive:
        raise HTTPException(status_code=400, detail="Update contains spam/abusive content")

    update = {
        "id": str(uuid.uuid4()),
        "author_email": auth_email,
        "text": update_text,
        "is_public": is_public,
        "created_at": datetime.now(timezone.utc).isoformat()
    }
    c.setdefault("updates", []).append(update)
    return {"id": update["id"], "created_at": update["created_at"], "is_public": is_public}

# -------------------------
# Manual interactive tester (replaces automated run_tests)
# -------------------------
import httpx
from tkinter import Tk, filedialog
import getpass

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

session = {"token": None, "role": None, "email": None}


def select_file(title="Select a file"):
    root = Tk()
    root.withdraw()
    root.attributes('-topmost', True)
    path = filedialog.askopenfilename(title=title)
    root.destroy()
    return path


def api_post(path, json=None, files=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.post(f"{BASE_URL}{path}", json=json, files=files, headers=headers)


def api_get(path, params=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.get(f"{BASE_URL}{path}", params=params, headers=headers)


def api_put(path, json=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.put(f"{BASE_URL}{path}", json=json, headers=headers)


def student_register_cli():
    print("\n-- Student Registration --")
    roll = input("Roll No: ").strip()
    name = input("Full Name: ").strip()
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ").strip()
    gender = input("Gender (Male/Female/Other): ").strip()
    stay = input("Stay Type (Hostel/Day Scholar): ").strip()
    year = input("Year (1st Year/2nd Year/3rd Year/4th Year): ").strip()
    dept = input("Department code (CSE/ECE/MECH/CIVIL/IT): ").strip()
    payload = {
        "roll_no": roll,
        "name": name,
        "email": email,
        "password": password,
        "gender": gender,
        "stay_type": stay,
        "year": year,
        "department_id": dept
    }
    resp = api_post("/api/students/register", json=payload)
    print(resp.status_code, resp.text)
    if resp.status_code == 201:
        data = resp.json()
        print("Registered. Token:", data.get("token")[:24], "...")
    return resp


def student_login_cli():
    print("\n-- Student Login --")
    identifier = input("Email or Roll No: ").strip()
    password = getpass.getpass("Password: ").strip()
    resp = api_post("/api/students/login", json={"email_or_roll_no": identifier, "password": password})
    print(resp.status_code, resp.text)
    if resp.status_code == 200:
        data = resp.json()
        session["token"] = data.get("token")
        session["role"] = "student"
        session["email"] = data.get("email")
        print("Logged in as:", data.get("name"))
    return resp


def submit_complaint_cli():
    if not session.get("token"):
        print("Login required")
        return
    print("\n-- Submit Complaint (AI will categorize) --")
    text = input("Complaint text: ").strip()
    visibility = input("Visibility (Private/Department/Public) [Public]: ").strip() or "Public"
    payload = {"original_text": text, "visibility": visibility}
    resp = api_post("/api/complaints/submit", json=payload, token=session["token"])
    print(resp.status_code, resp.text)
    return resp


def view_my_complaints_cli():
    if not session.get("token"):
        print("Login required")
        return
    resp = api_get("/api/students/my-complaints", token=session["token"])
    print(resp.status_code)
    try:
        for c in resp.json().get("complaints", []):
            print(f"- ID: {c['id']} | Status: {c.get('status')} | Priority: {c.get('priority')} | Category: {c.get('category', {}).get('name')}")
    except Exception:
        print(resp.text)
    return resp


def view_public_feed_cli():
    if not session.get("token"):
        print("Login required")
        return
    stay = input("Filter by stay_type (Hostel/Day Scholar) [skip]: ").strip() or None
    dept = input("Filter by department code (CSE/ECE/...) [skip]: ").strip() or None
    params = {}
    if stay:
        params["stay_type"] = stay
    if dept:
        params["department"] = dept
    resp = api_get("/api/complaints/public-feed", params=params, token=session["token"])
    print(resp.status_code)
    try:
        for c in resp.json().get("complaints", []):
            print(f"- ID: {c['id']} | Student: {c.get('student_email')} | Text: {c.get('rephrased_text')[:80]} | Up/Down: {c.get('upvotes')}/{c.get('downvotes')}")
    except Exception:
        print(resp.text)
    return resp


def vote_complaint_cli():
    if not session.get("token"):
        print("Login required")
        return
    cid = input("Complaint ID to vote: ").strip()
    v = input("Vote type (Upvote/Downvote): ").strip()
    resp = api_post(f"/api/complaints/{cid}/vote", json={"vote_type": v}, token=session["token"])
    print(resp.status_code, resp.text)
    return resp


def upload_image_cli():
    if not session.get("token"):
        print("Login required")
        return
    cid = input("Complaint ID to attach image: ").strip()
    path = select_file("Select image file (jpg/png)")
    if not path:
        print("No file selected")
        return
    with open(path, "rb") as f:
        files = {"file": (path.split("/")[-1], f, "image/jpeg")}
        # use httpx directly to send files with Authorization header
        headers = {"Authorization": f"Bearer {session['token']}"}
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(f"{BASE_URL}/api/complaints/{cid}/upload-image", files=files, headers=headers)
    print(resp.status_code, resp.text)
    return resp


def authority_login_cli():
    print("\n-- Authority Login --")
    email = input("Email: ").strip()
    password = getpass.getpass("Password: ").strip()
    resp = api_post("/api/authorities/login", json={"email": email, "password": password})
    print(resp.status_code, resp.text)
    if resp.status_code == 200:
        session["token"] = resp.json().get("token")
        session["role"] = "authority"
        session["email"] = email
        print("Authority logged in:", resp.json().get("name"))
    return resp


def authority_view_assigned_cli():
    if not session.get("token"):
        print("Login required")
        return
    resp = api_get("/api/authorities/my-complaints", token=session["token"])
    print(resp.status_code)
    try:
        for c in resp.json().get("complaints", []):
            print(f"- ID: {c['id']} | Student: {c.get('student_email')} | Status: {c.get('status')} | Category: {c.get('category', {}).get('name')}")
    except Exception:
        print(resp.text)
    return resp


def authority_update_status_cli():
    if not session.get("token"):
        print("Login required")
        return
    cid = input("Complaint ID to update: ").strip()
    status = input("New status (Raised/In Progress/Resolved/Closed/Spam): ").strip()
    reason = input("Reason (optional): ").strip()
    resp = api_put(f"/api/authorities/complaints/{cid}/status", json={"status": status, "reason": reason}, token=session["token"])
    print(resp.status_code, resp.text)
    return resp


def logout_cli():
    session["token"] = None
    session["role"] = None
    session["email"] = None
    print("Logged out")


def main_menu():
    while True:
        print("\n=== CampusVoice Manual Tester ===")
        print("1) Student: Register")
        print("2) Student: Login")
        print("3) Student: Submit Complaint")
        print("4) Student: View My Complaints")
        print("5) Student: View Public Feed")
        print("6) Student: Vote on Complaint")
        print("7) Student: Upload Image to Complaint")
        print("8) Authority: Login")
        print("9) Authority: View Assigned Complaints")
        print("10) Authority: Update Complaint Status")
        print("11) Logout")
        print("0) Exit")
        choice = input("Choose: ").strip()
        try:
            if choice == "1":
                student_register_cli()
            elif choice == "2":
                student_login_cli()
            elif choice == "3":
                submit_complaint_cli()
            elif choice == "4":
                view_my_complaints_cli()
            elif choice == "5":
                view_public_feed_cli()
            elif choice == "6":
                vote_complaint_cli()
            elif choice == "7":
                upload_image_cli()
            elif choice == "8":
                authority_login_cli()
            elif choice == "9":
                authority_view_assigned_cli()
            elif choice == "10":
                authority_update_status_cli()
            elif choice == "11":
                logout_cli()
            elif choice == "0":
                break
            else:
                print("Invalid choice")
        except Exception as e:
            print("Error:", e)


def automated_demo():
    """Automated demo: register 3 students, perform full flows, and print details."""
    from fastapi.testclient import TestClient
    from io import BytesIO
    from PIL import Image
    client = TestClient(app)

    students = [
        {"roll_no": "23CS001", "name": "Anita Rao", "email": "anita@college.edu", "password": "Pass@1234",
         "gender": "Female", "stay_type": "Hostel", "year": "1st Year", "department_id": "CSE"},
        {"roll_no": "22EC045", "name": "Ravi Kumar", "email": "ravi@college.edu", "password": "Pass@1234",
         "gender": "Male", "stay_type": "Day Scholar", "year": "2nd Year", "department_id": "ECE"},
        {"roll_no": "21ME110", "name": "Sonal Mehta", "email": "sonal@college.edu", "password": "Pass@1234",
         "gender": "Female", "stay_type": "Hostel", "year": "3rd Year", "department_id": "MECH"},
    ]

    print("\n=== AUTOMATED DEMO: Registering 3 students ===")
    tokens = {}
    for s in students:
        resp = client.post("/api/students/register", json=s)
        print(f"Register {s['email']}: {resp.status_code} {resp.text}")
        assert resp.status_code == 201, "Registration failed"
        tokens[s["email"]] = resp.json()["token"]

    print("\n=== Logging students in (to refresh tokens) ===")
    for s in students:
        resp = client.post("/api/students/login", json={"email_or_roll_no": s["email"], "password": s["password"]})
        print(f"Login {s['email']}: {resp.status_code} {resp.text}")
        tokens[s["email"]] = resp.json()["token"]

    print("\n=== Submitting complaints ===")
    complaints = {}
    # Anita (Hostel -> likely Warden)
    resp = client.post("/api/complaints/submit",
                       json={"original_text": "No hot water in hostel block A for two days.", "visibility": "Public"},
                       headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Anita submit:", resp.status_code, resp.json())
    complaints["anita"] = resp.json()["complaint_id"]

    # Ravi (Day scholar, ECE -> department/general)
    resp = client.post("/api/complaints/submit",
                       json={"original_text": "ECE lab equipment malfunctioning, projector not working.", "visibility": "Public"},
                       headers={"Authorization": f"Bearer {tokens['ravi@college.edu']}"})
    print("Ravi submit:", resp.status_code, resp.json())
    complaints["ravi"] = resp.json()["complaint_id"]

    # Sonal (MECH hostel maintenance)
    resp = client.post("/api/complaints/submit",
                       json={"original_text": "Mess food quality is poor and water leakage in hostel corridor.", "visibility": "Public"},
                       headers={"Authorization": f"Bearer {tokens['sonal@college.edu']}"})
    print("Sonal submit:", resp.status_code, resp.json())
    complaints["sonal"] = resp.json()["complaint_id"]

    print("\n=== Each student views their complaints ===")
    for s in students:
        resp = client.get("/api/students/my-complaints", headers={"Authorization": f"Bearer {tokens[s['email']]}"})
        # fallback if header formatting issue
        if resp.status_code != 200:
            resp = client.get("/api/students/my-complaints", headers={"Authorization": f"Bearer {tokens[s['email']]}"})
        print(f"{s['email']} my complaints: {resp.status_code} -> {resp.json()}")

    print("\n=== Public feed (no filters) ===")
    resp = client.get("/api/complaints/public-feed", headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Public feed:", resp.status_code, resp.json())

    print("\n=== Public feed filtered: stay_type=Hostel ===")
    resp = client.get("/api/complaints/public-feed", params={"stay_type": "Hostel"},
                      headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Filtered (Hostel):", resp.status_code, resp.json())

    print("\n=== Voting: Ravi upvotes Anita's complaint; Sonal upvotes Ravi's complaint ===")
    resp = client.post(f"/api/complaints/{complaints['anita']}/vote", json={"vote_type": "Upvote"},
                       headers={"Authorization": f"Bearer {tokens['ravi@college.edu']}"})
    print("Ravi upvotes Anita:", resp.status_code, resp.json())

    resp = client.post(f"/api/complaints/{complaints['ravi']}/vote", json={"vote_type": "Upvote"},
                       headers={"Authorization": f"Bearer {tokens['sonal@college.edu']}"})
    print("Sonal upvotes Ravi:", resp.status_code, resp.json())

    print("\n=== Verify vote counts reflected in public feed ===")
    resp = client.get("/api/complaints/public-feed", headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Public feed after votes:", resp.status_code, resp.json())

    print("\n=== Upload image to Anita's complaint (verified) ===")
    # create a small image in memory
    img = Image.new("RGB", (120, 80), color="green")
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    files = {"file": ("evidence.jpg", buf, "image/jpeg")}
    resp = client.post(f"/api/complaints/{complaints['anita']}/upload-image",
                       files=files,
                       headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Upload response:", resp.status_code, resp.json())

    print("\n=== Upload image to spammy complaint to show rejection ===")
    # Create spammy complaint then upload
    resp = client.post("/api/complaints/submit",
                       json={"original_text": "spam spam fake data spam", "visibility": "Public"},
                       headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    spam_id = resp.json()["complaint_id"]
    img2 = Image.new("RGB", (40, 40), color="red")
    buf2 = BytesIO()
    img2.save(buf2, format="JPEG")
    buf2.seek(0)
    files2 = {"file": ("spam.jpg", buf2, "image/jpeg")}
    resp = client.post(f"/api/complaints/{spam_id}/upload-image", files=files2,
                       headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Spam upload:", resp.status_code, resp.json())

    print("\n=== Authority logs in and views assigned complaints ===")
    resp = client.post("/api/authorities/login", json={"email": "warden@college.edu", "password": "Warden@123"})
    print("Authority login:", resp.status_code, resp.json())
    auth_token = resp.json()["token"]
    resp = client.get("/api/authorities/my-complaints", headers={"Authorization": f"Bearer {auth_token}"})
    print("Authority assigned complaints:", resp.status_code, resp.json())

    print("\n=== Authority updates Anita's complaint status to 'In Progress' ===")
    resp = client.put(f"/api/authorities/complaints/{complaints['anita']}/status",
                      json={"status": "In Progress", "reason": "Assigned to Warden"},
                      headers={"Authorization": f"Bearer {auth_token}"})
    print("Status update:", resp.status_code, resp.json())

    print("\n=== Verify student sees updated status ===")
    resp = client.get("/api/students/my-complaints", headers={"Authorization": f"Bearer {tokens['anita@college.edu']}"})
    print("Anita my complaints after update:", resp.status_code, resp.json())

    print("\n=== DEMO COMPLETE ===\n")


if __name__ == "__main__":
    # Run automated demo first
    try:
        automated_demo()
    except AssertionError as e:
        print("Automated demo encountered an error:", e)
    except Exception as e:
        print("Automated demo failed:", e)

    # Then start interactive manual tester
    print("Manual tester - interacts with API at", BASE_URL)
    print("Make sure your FastAPI server is running (python main.py).")
    main_menu()

@app.post("/testing/cleanup")
async def testing_cleanup():
    """
    Testing-only endpoint: clear in-memory stores used by the test harness.
    Use this from client_test.py to reset state between runs.
    """
    counts = {
        "students": len(STUDENTS),
        "tokens": len(TOKENS),
        "complaints": len(COMPLAINTS),
        "votes": len(VOTES),
        "authorities": len(AUTHORITIES),
    }
    STUDENTS.clear()
    TOKENS.clear()
    COMPLAINTS.clear()
    VOTES.clear()
    AUTHORITIES.clear()
    return {"status": "ok", "cleared_counts": counts}

# Ensure default authority records exist so assigned_authority_email points to a real authority
@app.on_event("startup")
def _init_default_authorities():
	roles = set(DEFAULT_CATEGORY_ROUTING.values())
	for role in roles:
		email = f"{role.replace(' ', '').lower()}@college.edu"
		if email.lower() not in AUTHORITIES:
			# default password pattern matches examples (e.g. "Warden@123")
			default_password = f"{role}@123"
			AUTHORITIES[email.lower()] = {
				"email": email,
				"name": role.replace(" ", "").lower(),
				"password": default_password,
				"authority_type": role,
				"authority_level": AUTHORITY_LEVELS.get(role, 50),
			}
