"""
CampusVoice - Streamlit Client
================================
Run:     streamlit run streamlit_app.py
Backend: python main.py  (port 8000)
"""

import streamlit as st
import requests
from datetime import datetime, date

# ════════════════════════════════════════════════════════════════
# CONFIGURATION
# ════════════════════════════════════════════════════════════════

BASE_URL = "http://localhost:8000"
API = f"{BASE_URL}/api"

# Must match constants.py DEPARTMENTS (all 13, seeded by connection.py)
DEPARTMENTS = {
    1: "CSE - Computer Science & Engineering",
    2: "ECE - Electronics & Communication Engineering",
    3: "RAA - Robotics and Automation",
    4: "MECH - Mechanical Engineering",
    5: "EEE - Electrical & Electronics Engineering",
    6: "EIE - Electronics & Instrumentation Engineering",
    7: "BIO - Biomedical Engineering",
    8: "AERO - Aeronautical Engineering",
    9: "CIVIL - Civil Engineering",
    10: "IT - Information Technology",
    11: "MBA - Management Studies",
    12: "AIDS - Artificial Intelligence and Data Science",
    13: "MTECH_CSE - M.Tech in Computer Science and Engineering",
}

# Must match the 5 categories seeded via lifespan/setup
# (Men's Hostel, Women's Hostel, General, Department, Disciplinary Committee)
CATEGORIES = {
    1: "Men's Hostel",
    2: "Women's Hostel",
    3: "General",
    4: "Department",
    5: "Disciplinary Committee",
}

STATUSES = ["Raised", "In Progress", "Resolved", "Closed", "Spam"]
PRIORITIES = ["Low", "Medium", "High", "Critical"]
VISIBILITY_OPTIONS = ["Public", "Department", "Private"]
GENDERS = ["Male", "Female", "Other"]
STAY_TYPES = ["Hostel", "Day Scholar"]

VALID_TRANSITIONS = {
    "Raised": ["In Progress", "Spam", "Closed"],
    "In Progress": ["Resolved", "Raised", "Closed"],
    "Resolved": ["Closed", "Raised"],
    "Spam": ["Closed"],
}


# ════════════════════════════════════════════════════════════════
# SESSION STATE
# ════════════════════════════════════════════════════════════════

def init_session():
    defaults = dict(
        token=None, role=None, user=None,
        selected_complaint=None, detail_source=None,
    )
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ════════════════════════════════════════════════════════════════
# API HELPERS
# ════════════════════════════════════════════════════════════════

def api(method, path, json_body=None, data=None, files=None, params=None, timeout=60):
    """Make API request. Returns requests.Response or None on connection error."""
    headers = {}
    if st.session_state.get("token"):
        headers["Authorization"] = f"Bearer {st.session_state.token}"
    try:
        if path.startswith("/health"):
            url = f"{BASE_URL}{path}"
        else:
            url = f"{API}{path}"
        return requests.request(
            method, url, headers=headers,
            json=json_body, data=data, files=files, params=params,
            timeout=timeout,
        )
    except requests.ConnectionError:
        return None
    except Exception:
        return None


def ok(resp):
    return resp is not None and resp.status_code < 400


def show_error(resp):
    if resp is None:
        st.error("Cannot connect to backend. Is `python main.py` running on port 8000?")
        return
    try:
        body = resp.json()
        msg = body.get("error") or body.get("detail") or f"Error {resp.status_code}"
        if isinstance(msg, dict):
            msg = msg.get("error") or msg.get("reason") or str(msg)
        st.error(msg)
        details = body.get("details") or {}
        for ve in details.get("validation_errors", []):
            st.caption(f"  {ve.get('field', '?')}: {ve.get('message', '?')}")
    except Exception:
        st.error(f"Error {resp.status_code}: {resp.text[:300]}")


def logout():
    for k in ["token", "role", "user", "selected_complaint", "detail_source"]:
        st.session_state[k] = None
    st.rerun()


# ════════════════════════════════════════════════════════════════
# REUSABLE UI COMPONENTS
# ════════════════════════════════════════════════════════════════

def complaint_card(c, idx, prefix="comp"):
    """Render a single complaint card. Returns True if View was clicked."""
    cat = c.get("category_name") or CATEGORIES.get(c.get("category_id"), "Unknown")
    comp_status = c.get("status", "?")
    priority = c.get("priority", "?")
    text = c.get("rephrased_text") or c.get("original_text") or ""
    up = c.get("upvotes", 0)
    down = c.get("downvotes", 0)
    submitted = (c.get("submitted_at") or "")[:16].replace("T", " ")

    status_colors = {
        "Raised": "orange", "In Progress": "blue", "Resolved": "green",
        "Closed": "gray", "Spam": "red",
    }
    sc = status_colors.get(comp_status, "gray")

    col1, col2, col3, col4, col5 = st.columns([2, 1.5, 1, 1.2, 0.8])
    with col1:
        st.markdown(f"**{cat}**")
        st.caption(text[:120] + ("..." if len(text) > 120 else ""))
    with col2:
        st.markdown(f":{sc}[{comp_status}]")
        st.caption(submitted)
    with col3:
        st.caption(f"Priority: **{priority}**")
    with col4:
        st.caption(f"+{up}  -{down}")
        if c.get("has_image"):
            st.caption("Has image")
    with col5:
        if st.button("View", key=f"{prefix}_{idx}"):
            st.session_state.selected_complaint = c["id"]
            st.rerun()
    st.divider()


def complaint_card_with_voting(c, idx, prefix="comp"):
    """Render complaint card with inline voting buttons."""
    cat = c.get("category_name") or CATEGORIES.get(c.get("category_id"), "Unknown")
    comp_status = c.get("status", "?")
    priority = c.get("priority", "?")
    text = c.get("rephrased_text") or c.get("original_text") or ""
    up = c.get("upvotes", 0)
    down = c.get("downvotes", 0)
    submitted = (c.get("submitted_at") or "")[:16].replace("T", " ")
    cid = c.get("id")

    status_colors = {
        "Raised": "orange", "In Progress": "blue", "Resolved": "green",
        "Closed": "gray", "Spam": "red",
    }
    sc = status_colors.get(comp_status, "gray")

    col1, col2, col3, col4, col5 = st.columns([2.5, 1.2, 1.5, 1.5, 0.8])
    with col1:
        st.markdown(f"**{cat}**")
        st.caption(text[:100] + ("..." if len(text) > 100 else ""))
    with col2:
        st.markdown(f":{sc}[{comp_status}]")
        st.caption(submitted)
    with col3:
        st.caption(f"Priority: {priority}")
        if c.get("has_image"):
            st.caption("Has image")
    with col4:
        vc1, vc2, vc3 = st.columns(3)
        with vc1:
            if st.button(f"+{up}", key=f"{prefix}_up_{idx}", help="Upvote"):
                r = api("POST", f"/complaints/{cid}/vote", json_body={"vote_type": "Upvote"})
                if ok(r):
                    st.rerun()
                else:
                    show_error(r)
        with vc2:
            if st.button(f"-{down}", key=f"{prefix}_dn_{idx}", help="Downvote"):
                r = api("POST", f"/complaints/{cid}/vote", json_body={"vote_type": "Downvote"})
                if ok(r):
                    st.rerun()
                else:
                    show_error(r)
        with vc3:
            if st.button("X", key=f"{prefix}_rm_{idx}", help="Remove vote"):
                r = api("DELETE", f"/complaints/{cid}/vote")
                if ok(r):
                    st.rerun()
    with col5:
        if st.button("View", key=f"{prefix}_v_{idx}"):
            st.session_state.selected_complaint = cid
            st.rerun()
    st.divider()


def pagination_controls(total, skip, limit, key_prefix="pg"):
    """Show pagination and return (new_skip, new_limit)."""
    total_pages = max(1, -(-total // limit))
    current_page = (skip // limit) + 1

    cols = st.columns([1, 2, 1])
    with cols[0]:
        if current_page > 1:
            if st.button("Previous", key=f"{key_prefix}_prev"):
                return max(0, skip - limit), limit
    with cols[1]:
        st.caption(f"Page {current_page} of {total_pages} ({total} total)")
    with cols[2]:
        if current_page < total_pages:
            if st.button("Next", key=f"{key_prefix}_next"):
                return skip + limit, limit
    return skip, limit


# ════════════════════════════════════════════════════════════════
# AUTH PAGES
# ════════════════════════════════════════════════════════════════

def page_auth():
    st.title("CampusVoice")
    st.caption("Campus Complaint Management System")

    tab_sl, tab_al, tab_reg = st.tabs(["Student Login", "Authority Login", "Student Register"])

    # -- Student Login --
    with tab_sl:
        with st.form("student_login"):
            email_or_roll = st.text_input("Email or Roll Number")
            password = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login as Student")
        if submitted:
            if not email_or_roll or not password:
                st.warning("Please fill in all fields.")
            else:
                resp = api("POST", "/students/login", json_body={
                    "email_or_roll_no": email_or_roll.strip(),
                    "password": password,
                })
                if ok(resp):
                    d = resp.json()
                    st.session_state.token = d["token"]
                    st.session_state.role = "Student"
                    st.session_state.user = d
                    st.success(f"Welcome, {d['name']}!")
                    st.rerun()
                else:
                    show_error(resp)

    # -- Authority / Admin Login --
    with tab_al:
        with st.form("authority_login"):
            a_email = st.text_input("Email")
            a_pass = st.text_input("Password", type="password")
            submitted = st.form_submit_button("Login as Authority / Admin")
        if submitted:
            if not a_email or not a_pass:
                st.warning("Please fill in all fields.")
            else:
                resp = api("POST", "/authorities/login", json_body={
                    "email": a_email.strip(),
                    "password": a_pass,
                })
                if ok(resp):
                    d = resp.json()
                    st.session_state.token = d["token"]
                    # Detect admin from authority_type
                    if d.get("authority_type") == "Admin":
                        st.session_state.role = "Admin"
                    else:
                        st.session_state.role = "Authority"
                    st.session_state.user = d
                    st.success(f"Welcome, {d['name']}!")
                    st.rerun()
                else:
                    show_error(resp)

    # -- Student Register --
    with tab_reg:
        with st.form("student_register"):
            r_roll = st.text_input("Roll Number (e.g. 22CS231)")
            r_name = st.text_input("Full Name")
            r_email = st.text_input("Email (@srec.ac.in)")
            r_pass = st.text_input("Password (min 8, 1 upper, 1 lower, 1 digit)", type="password")
            rc1, rc2 = st.columns(2)
            r_gender = rc1.selectbox("Gender", GENDERS)
            r_stay = rc2.selectbox("Stay Type", STAY_TYPES)
            rc3, rc4 = st.columns(2)
            r_dept = rc3.selectbox("Department", options=list(DEPARTMENTS.keys()),
                                   format_func=lambda x: DEPARTMENTS[x])
            r_year = rc4.number_input("Year", min_value=1, max_value=10, value=1)
            submitted = st.form_submit_button("Register")

        if submitted:
            if not all([r_roll, r_name, r_email, r_pass]):
                st.warning("Please fill in all required fields.")
            else:
                resp = api("POST", "/students/register", json_body={
                    "roll_no": r_roll.strip(),
                    "name": r_name.strip(),
                    "email": r_email.strip(),
                    "password": r_pass,
                    "gender": r_gender,
                    "stay_type": r_stay,
                    "department_id": r_dept,
                    "year": r_year,
                })
                if ok(resp):
                    d = resp.json()
                    st.session_state.token = d["token"]
                    st.session_state.role = "Student"
                    st.session_state.user = d
                    st.success(f"Registered successfully! Welcome, {d['name']}!")
                    st.rerun()
                else:
                    show_error(resp)


# ════════════════════════════════════════════════════════════════
# STUDENT PAGES
# ════════════════════════════════════════════════════════════════

def page_student_dashboard():
    st.header("Dashboard")
    resp = api("GET", "/students/stats")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return
    s = resp.json()

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total", s.get("total_complaints", 0))
    c2.metric("Raised", s.get("raised", 0))
    c3.metric("In Progress", s.get("in_progress", 0))
    c4.metric("Resolved", s.get("resolved", 0))
    c5.metric("Closed", s.get("closed", 0))
    c6.metric("Spam", s.get("spam", 0))

    st.metric("Total Votes Cast", s.get("total_votes_cast", 0))


def page_submit_complaint():
    st.header("Submit Complaint")

    # Filter categories based on student context
    user = st.session_state.user or {}
    stay_type = user.get("stay_type", "")
    gender = user.get("gender", "")

    available_categories = {}
    for cat_id, cat_name in CATEGORIES.items():
        # Day scholars cannot submit hostel complaints
        if stay_type == "Day Scholar" and cat_name in ("Men's Hostel", "Women's Hostel"):
            continue
        # Hostel students only see their gender's hostel category
        if stay_type == "Hostel":
            if gender == "Male" and cat_name == "Women's Hostel":
                continue
            if gender == "Female" and cat_name == "Men's Hostel":
                continue
        available_categories[cat_id] = cat_name

    with st.form("submit_complaint"):
        category = st.selectbox(
            "Category", options=list(available_categories.keys()),
            format_func=lambda x: available_categories[x],
        )
        text = st.text_area(
            "Describe your complaint (10-2000 characters)",
            max_chars=2000, height=150,
        )
        visibility = st.selectbox("Visibility", VISIBILITY_OPTIONS)
        image = st.file_uploader(
            "Attach image (optional, max 5MB)",
            type=["jpg", "jpeg", "png", "gif", "webp"],
        )
        submitted = st.form_submit_button("Submit Complaint")

    if submitted:
        if not text or len(text.strip()) < 10:
            st.warning("Complaint text must be at least 10 characters.")
            return

        form_data = {
            "category_id": str(category),
            "original_text": text.strip(),
            "visibility": visibility,
        }
        files = {}
        if image:
            files["image"] = (image.name, image.getvalue(), image.type)

        with st.spinner("Submitting... LLM is analyzing your complaint..."):
            resp = api("POST", "/complaints/submit",
                       data=form_data, files=files if files else None)

        if ok(resp):
            d = resp.json()
            st.success(d.get("message", "Complaint submitted successfully!"))
            st.write("**Complaint ID:**", d.get("id"))
            if d.get("rephrased_text"):
                st.info(f"**Rephrased:** {d['rephrased_text']}")
            st.write("**Priority:**", d.get("priority"))
            st.write("**Assigned to:**", d.get("assigned_authority"))
            if d.get("has_image"):
                st.write("**Image verified:**", d.get("image_verified"))
                if d.get("image_verification_message"):
                    st.caption(d["image_verification_message"])
            if d.get("image_was_required"):
                st.warning(f"Image requirement: {d.get('image_requirement_reasoning', '')}")
        else:
            show_error(resp)


def page_my_complaints():
    st.header("My Complaints")

    col1, col2, col3 = st.columns([1, 1, 2])
    status_filter = col1.selectbox("Filter by status", ["All"] + STATUSES, key="mc_status")
    skip = col2.number_input("Skip", min_value=0, value=0, step=20, key="mc_skip")
    limit = 20

    params = {"skip": skip, "limit": limit}
    if status_filter != "All":
        params["status_filter"] = status_filter

    resp = api("GET", "/students/my-complaints", params=params)
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    complaints = d.get("complaints", [])
    total = d.get("total", 0)

    st.caption(f"Showing {len(complaints)} of {total} complaints")

    if not complaints:
        st.info("No complaints found.")
        return

    for i, c in enumerate(complaints):
        complaint_card(c, i, prefix="mc")

    pagination_controls(total, skip, limit, key_prefix="mc_pg")


def page_public_feed():
    st.header("Public Feed")

    col1, _ = st.columns([1, 3])
    skip = col1.number_input("Skip", min_value=0, value=0, step=20, key="pf_skip")
    limit = 20

    resp = api("GET", "/complaints/public-feed", params={"skip": skip, "limit": limit})
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    complaints = d.get("complaints", [])
    total = d.get("total", 0)

    st.caption(f"Showing {len(complaints)} of {total} complaints")

    if not complaints:
        st.info("No public complaints found.")
        return

    for i, c in enumerate(complaints):
        complaint_card_with_voting(c, i, prefix="pf")

    pagination_controls(total, skip, limit, key_prefix="pf_pg")


def page_advanced_search():
    st.header("Advanced Search")

    with st.form("adv_search"):
        c1, c2, c3 = st.columns(3)
        status_val = c1.selectbox("Status", ["Any"] + STATUSES)
        priority = c2.selectbox("Priority", ["Any"] + PRIORITIES)
        cat_id = c3.selectbox("Category", ["Any"] + list(CATEGORIES.keys()),
                              format_func=lambda x: "Any" if x == "Any" else CATEGORIES[x])

        c4, c5 = st.columns(2)
        has_img = c4.selectbox("Has Image", ["Any", "Yes", "No"])
        img_verified = c5.selectbox("Image Verified", ["Any", "Yes", "No"])

        search = st.text_input("Search text (min 2 chars)")

        c6, c7 = st.columns(2)
        date_from = c6.date_input("Date from", value=None)
        date_to = c7.date_input("Date to", value=None)

        submitted = st.form_submit_button("Search")

    if submitted:
        params = {"skip": 0, "limit": 50}
        if status_val != "Any":
            params["status"] = status_val
        if priority != "Any":
            params["priority"] = priority
        if cat_id != "Any":
            params["category_id"] = cat_id
        if has_img == "Yes":
            params["has_image"] = "true"
        elif has_img == "No":
            params["has_image"] = "false"
        if img_verified == "Yes":
            params["image_verified"] = "true"
        elif img_verified == "No":
            params["image_verified"] = "false"
        if search and len(search.strip()) >= 2:
            params["search"] = search.strip()
        if date_from:
            params["date_from"] = f"{date_from}T00:00:00"
        if date_to:
            params["date_to"] = f"{date_to}T23:59:59"

        resp = api("GET", "/complaints/filter/advanced", params=params)
        if resp is None:
            st.error("Cannot connect to backend.")
            return
        if not ok(resp):
            show_error(resp)
            return

        d = resp.json()
        complaints = d.get("complaints", [])
        total = d.get("total", 0)
        st.caption(f"Found {total} results")

        if not complaints:
            st.info("No complaints match your filters.")
        for i, c in enumerate(complaints):
            complaint_card(c, i, prefix="as")


def page_notifications():
    st.header("Notifications")

    col1, col2 = st.columns([1, 1])
    unread_only = col1.checkbox("Unread only", value=False)
    if col2.button("Mark All Read"):
        r = api("PUT", "/students/notifications/mark-all-read")
        if ok(r):
            st.success(r.json().get("message", "Done"))
            st.rerun()
        else:
            show_error(r)

    resp = api("GET", "/students/notifications",
               params={"skip": 0, "limit": 50, "unread_only": str(unread_only).lower()})
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    notifications = d.get("notifications", [])
    total = d.get("total", 0)
    unread = d.get("unread_count", 0)

    st.caption(f"Total: {total} | Unread: {unread}")

    if not notifications:
        st.info("No notifications.")
        return

    for i, n in enumerate(notifications):
        is_read = n.get("is_read", False)
        marker = "" if is_read else " (unread)"
        msg = n.get("message", "")
        created = (n.get("created_at") or "")[:16].replace("T", " ")

        cols = st.columns([4, 1, 1])
        with cols[0]:
            st.write(f"**{msg}**{marker}" if not is_read else msg)
            st.caption(created)
        with cols[1]:
            if not is_read:
                if st.button("Mark Read", key=f"nr_{i}"):
                    r = api("PUT", f"/students/notifications/{n['id']}/read")
                    if ok(r):
                        st.rerun()
                    else:
                        show_error(r)
        with cols[2]:
            if st.button("Delete", key=f"nd_{i}"):
                r = api("DELETE", f"/students/notifications/{n['id']}")
                if ok(r):
                    st.rerun()
                else:
                    show_error(r)
        st.divider()


def page_student_profile():
    st.header("My Profile")

    resp = api("GET", "/students/profile")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    p = resp.json()

    c1, c2 = st.columns(2)
    c1.write(f"**Roll No:** {p.get('roll_no')}")
    c1.write(f"**Name:** {p.get('name')}")
    c1.write(f"**Email:** {p.get('email')}")
    c1.write(f"**Gender:** {p.get('gender')}")

    c2.write(f"**Stay Type:** {p.get('stay_type')}")
    dept_name = p.get("department_name") or DEPARTMENTS.get(p.get("department_id"), "?")
    c2.write(f"**Department:** {dept_name}")
    c2.write(f"**Year:** {p.get('year', '-')}")
    c2.write(f"**Active:** {p.get('is_active')}")

    st.divider()
    st.subheader("Update Profile")
    with st.form("update_profile"):
        new_name = st.text_input("Name", value=p.get("name", ""))
        new_email = st.text_input("Email", value=p.get("email", ""))
        new_phone = st.text_input("Phone (10 digits, starts 6-9)", value="")
        new_year = st.number_input("Year", min_value=1, max_value=10,
                                   value=p.get("year") or 1)
        submitted = st.form_submit_button("Update")

    if submitted:
        body = {}
        if new_name.strip() and new_name.strip() != p.get("name"):
            body["name"] = new_name.strip()
        if new_email.strip() and new_email.strip() != p.get("email"):
            body["email"] = new_email.strip()
        if new_phone.strip():
            body["phone"] = new_phone.strip()
        if new_year != p.get("year"):
            body["year"] = new_year

        if not body:
            st.info("No changes to update.")
        else:
            resp2 = api("PUT", "/students/profile", json_body=body)
            if ok(resp2):
                st.success("Profile updated!")
                st.rerun()
            else:
                show_error(resp2)


def page_change_password():
    st.header("Change Password")
    with st.form("change_pw"):
        old_pw = st.text_input("Current Password", type="password")
        new_pw = st.text_input("New Password (min 8, 1 upper, 1 lower, 1 digit)", type="password")
        confirm_pw = st.text_input("Confirm New Password", type="password")
        submitted = st.form_submit_button("Change Password")

    if submitted:
        if not all([old_pw, new_pw, confirm_pw]):
            st.warning("Please fill in all fields.")
        elif new_pw != confirm_pw:
            st.warning("Passwords do not match.")
        else:
            resp = api("POST", "/students/change-password", json_body={
                "old_password": old_pw,
                "new_password": new_pw,
                "confirm_password": confirm_pw,
            })
            if ok(resp):
                st.success("Password changed successfully!")
            else:
                show_error(resp)


# ════════════════════════════════════════════════════════════════
# COMPLAINT DETAIL - STUDENT VIEW
# ════════════════════════════════════════════════════════════════

def page_complaint_detail_student():
    cid = st.session_state.selected_complaint
    if st.button("Back to list"):
        st.session_state.selected_complaint = None
        st.rerun()

    resp = api("GET", f"/complaints/{cid}")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    c = resp.json()

    st.header(f"Complaint: {CATEGORIES.get(c.get('category_id'), c.get('category_name', 'Unknown'))}")
    st.caption(f"ID: {cid}")

    tab_info, tab_image, tab_history, tab_vote = st.tabs(
        ["Details", "Image", "History & Timeline", "Vote"]
    )

    # -- Details Tab --
    with tab_info:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Status:** {c.get('status')}")
            st.write(f"**Priority:** {c.get('priority')} (score: {c.get('priority_score', 0)})")
            st.write(f"**Visibility:** {c.get('visibility')}")
            st.write(f"**Assigned to:** {c.get('assigned_authority_name', '-')}")
        with col2:
            st.write(f"**Submitted:** {(c.get('submitted_at') or '')[:16]}")
            st.write(f"**Updated:** {(c.get('updated_at') or '')[:16]}")
            if c.get("resolved_at"):
                st.write(f"**Resolved:** {c['resolved_at'][:16]}")
            st.write(f"**Votes:** +{c.get('upvotes', 0)} / -{c.get('downvotes', 0)}")

        st.divider()
        st.subheader("Original Text")
        st.write(c.get("original_text", ""))
        if c.get("rephrased_text"):
            st.subheader("Rephrased Text")
            st.info(c["rephrased_text"])

        if c.get("status_updates"):
            st.subheader("Status Updates")
            for su in c["status_updates"]:
                st.write(f"  {su.get('old_status')} -> {su.get('new_status')}: {su.get('reason', '-')}")

    # -- Image Tab --
    with tab_image:
        if c.get("has_image"):
            st.write(f"**Filename:** {c.get('image_filename', '-')}")
            st.write(f"**Size:** {c.get('image_size', 0)} bytes")
            st.write(f"**Type:** {c.get('image_mimetype', '-')}")
            st.write(f"**Verification:** {c.get('image_verification_status', '-')}")

            img_resp = api("GET", f"/complaints/{cid}/image")
            if ok(img_resp):
                st.image(img_resp.content, caption="Complaint Image", use_container_width=True)
            else:
                st.warning("Could not load image.")

            if st.button("Load Thumbnail"):
                thumb_resp = api("GET", f"/complaints/{cid}/image", params={"thumbnail": "true"})
                if ok(thumb_resp):
                    st.image(thumb_resp.content, caption="Thumbnail (200x200)")

            if st.button("Re-verify Image"):
                with st.spinner("Verifying with LLM..."):
                    vr = api("POST", f"/complaints/{cid}/verify-image")
                if ok(vr):
                    vd = vr.json()
                    st.success(f"Verification: {vd.get('verification_status', '?')}")
                    st.write(vd.get("verification_message", ""))
                else:
                    show_error(vr)
        else:
            st.info("No image attached to this complaint.")
            own_roll = st.session_state.user.get("roll_no") if st.session_state.user else None
            complaint_roll = c.get("student_roll_no")
            if own_roll and complaint_roll and own_roll == complaint_roll:
                st.subheader("Upload Image")
                img_file = st.file_uploader(
                    "Select image", type=["jpg", "jpeg", "png", "gif", "webp"],
                    key="upload_img_detail",
                )
                if img_file and st.button("Upload"):
                    files = {"file": (img_file.name, img_file.getvalue(), img_file.type)}
                    with st.spinner("Uploading and verifying..."):
                        ur = api("POST", f"/complaints/{cid}/upload-image", files=files)
                    if ok(ur):
                        ud = ur.json()
                        st.success("Image uploaded!")
                        st.write(f"Verified: {ud.get('image_verified')}")
                        st.write(ud.get("verification_message", ""))
                        st.rerun()
                    else:
                        show_error(ur)

    # -- History Tab --
    with tab_history:
        st.subheader("Status History")
        hr = api("GET", f"/complaints/{cid}/status-history")
        if ok(hr):
            hd = hr.json()
            st.write(f"**Current Status:** {hd.get('current_status', '?')}")
            for su in hd.get("status_updates", []):
                st.write(
                    f"  {su.get('old_status')} -> **{su.get('new_status')}** "
                    f"| {su.get('reason', '-')} "
                    f"| by {su.get('updated_by', '?')} "
                    f"| {(su.get('updated_at') or '')[:16]}"
                )
            if not hd.get("status_updates"):
                st.caption("No status changes yet.")
        elif hr is not None:
            show_error(hr)

        st.divider()
        st.subheader("Timeline")
        tr = api("GET", f"/complaints/{cid}/timeline")
        if ok(tr):
            td = tr.json()
            for event in td.get("timeline", []):
                ts = (event.get("timestamp") or "")[:16].replace("T", " ")
                st.write(f"**{event.get('event')}** - {ts}")
                st.caption(event.get("description", ""))
                if event.get("reason"):
                    st.caption(f"Reason: {event['reason']}")
            if not td.get("timeline"):
                st.caption("No timeline events.")
        elif tr is not None:
            show_error(tr)

    # -- Vote Tab --
    with tab_vote:
        vr = api("GET", f"/complaints/{cid}/my-vote")
        current_vote = None
        if ok(vr):
            vd = vr.json()
            current_vote = vd.get("vote_type")
            if vd.get("has_voted"):
                st.write(f"**Your current vote:** {current_vote}")
            else:
                st.write("You haven't voted on this complaint.")

        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Upvote"):
                r = api("POST", f"/complaints/{cid}/vote",
                        json_body={"vote_type": "Upvote"})
                if ok(r):
                    rd = r.json()
                    st.success(f"Upvoted! +{rd.get('upvotes', 0)} -{rd.get('downvotes', 0)}")
                    st.rerun()
                else:
                    show_error(r)
        with col2:
            if st.button("Downvote"):
                r = api("POST", f"/complaints/{cid}/vote",
                        json_body={"vote_type": "Downvote"})
                if ok(r):
                    rd = r.json()
                    st.success(f"Downvoted! +{rd.get('upvotes', 0)} -{rd.get('downvotes', 0)}")
                    st.rerun()
                else:
                    show_error(r)
        with col3:
            if current_vote and st.button("Remove Vote"):
                r = api("DELETE", f"/complaints/{cid}/vote")
                if ok(r):
                    st.success("Vote removed!")
                    st.rerun()
                else:
                    show_error(r)


# ════════════════════════════════════════════════════════════════
# AUTHORITY PAGES
# ════════════════════════════════════════════════════════════════

def page_authority_dashboard():
    st.header("Authority Dashboard")

    resp = api("GET", "/authorities/dashboard")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    profile = d.get("profile", {})
    stats = d.get("stats", {})

    st.subheader(f"{profile.get('name', '?')} - {profile.get('authority_type', '?')}")
    if profile.get("designation"):
        st.caption(profile["designation"])

    c1, c2, c3, c4, c5, c6 = st.columns(6)
    c1.metric("Total Assigned", stats.get("total_assigned", 0))
    c2.metric("Pending", stats.get("pending", 0))
    c3.metric("In Progress", stats.get("in_progress", 0))
    c4.metric("Resolved", stats.get("resolved", 0))
    c5.metric("Closed", stats.get("closed", 0))
    c6.metric("Spam", stats.get("spam_flagged", 0))

    sc1, sc2, sc3 = st.columns(3)
    if stats.get("avg_resolution_time_hours") is not None:
        sc1.metric("Avg Resolution (hrs)", f"{stats['avg_resolution_time_hours']:.1f}")
    if stats.get("performance_rating") is not None:
        sc2.metric("Performance Rating", f"{stats['performance_rating']:.1f}")
    sc3.metric("Unread Notifications", d.get("unread_notifications", 0))

    recent = d.get("recent_complaints", [])
    if recent:
        st.divider()
        st.subheader("Recent Complaints")
        for i, c in enumerate(recent):
            cat = c.get("category_name") or CATEGORIES.get(c.get("category_id"), "?")
            text = c.get("rephrased_text") or c.get("original_text") or ""
            cols = st.columns([3, 1, 1])
            cols[0].write(f"**{cat}** - {c.get('status', '?')}")
            cols[0].caption(text[:100])
            cols[1].caption(f"Priority: {c.get('priority', '?')}")
            if cols[2].button("View", key=f"dash_recent_{i}"):
                st.session_state.selected_complaint = c.get("id")
                st.rerun()

    urgent = d.get("urgent_complaints", [])
    if urgent:
        st.divider()
        st.subheader("Urgent Complaints")
        for i, c in enumerate(urgent):
            cat = c.get("category_name") or CATEGORIES.get(c.get("category_id"), "?")
            text = c.get("rephrased_text") or c.get("original_text") or ""
            cols = st.columns([3, 1, 1])
            cols[0].write(f"**{cat}** - {c.get('status', '?')}")
            cols[0].caption(text[:100])
            cols[1].caption(f"Priority: {c.get('priority', '?')}")
            if cols[2].button("View", key=f"dash_urgent_{i}"):
                st.session_state.selected_complaint = c.get("id")
                st.rerun()


def page_authority_complaints():
    st.header("Assigned Complaints")

    col1, col2 = st.columns([1, 3])
    status_filter = col1.selectbox("Filter", ["All"] + STATUSES, key="ac_status")
    skip = col2.number_input("Skip", min_value=0, value=0, step=20, key="ac_skip")
    limit = 20

    params = {"skip": skip, "limit": limit}
    if status_filter != "All":
        params["status_filter"] = status_filter

    resp = api("GET", "/authorities/my-complaints", params=params)
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    complaints = d.get("complaints", [])
    total = d.get("total", 0)

    st.caption(f"Showing {len(complaints)} of {total}")

    if not complaints:
        st.info("No complaints assigned.")
        return

    for i, c in enumerate(complaints):
        complaint_card(c, i, prefix="ac")

    pagination_controls(total, skip, limit, key_prefix="ac_pg")


def page_authority_profile():
    st.header("Authority Profile")

    resp = api("GET", "/authorities/profile")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    p = resp.json()

    c1, c2 = st.columns(2)
    c1.write(f"**Name:** {p.get('name')}")
    c1.write(f"**Email:** {p.get('email')}")
    c1.write(f"**Phone:** {p.get('phone', '-')}")
    c1.write(f"**Type:** {p.get('authority_type')}")

    c2.write(f"**Designation:** {p.get('designation', '-')}")
    c2.write(f"**Level:** {p.get('authority_level')}")
    c2.write(f"**Department:** {p.get('department_name', '-')}")
    c2.write(f"**Active:** {p.get('is_active')}")


def page_authority_stats():
    st.header("Authority Statistics")

    resp = api("GET", "/authorities/stats")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    s = resp.json()
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Assigned", s.get("total_assigned", 0))
    c1.metric("Pending", s.get("pending", 0))
    c2.metric("In Progress", s.get("in_progress", 0))
    c2.metric("Resolved", s.get("resolved", 0))
    c3.metric("Closed", s.get("closed", 0))
    c3.metric("Spam Flagged", s.get("spam_flagged", 0))

    if s.get("avg_resolution_time_hours") is not None:
        st.metric("Avg Resolution Time (hrs)", f"{s['avg_resolution_time_hours']:.1f}")
    if s.get("performance_rating") is not None:
        st.metric("Performance Rating", f"{s['performance_rating']:.1f}")


# ════════════════════════════════════════════════════════════════
# COMPLAINT DETAIL - AUTHORITY VIEW
# ════════════════════════════════════════════════════════════════

def page_complaint_detail_authority():
    cid = st.session_state.selected_complaint
    if st.button("Back to list"):
        st.session_state.selected_complaint = None
        st.rerun()

    resp = api("GET", f"/authorities/complaints/{cid}")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    c = resp.json()

    st.header(f"Complaint: {CATEGORIES.get(c.get('category_id'), c.get('category_name', '?'))}")
    st.caption(f"ID: {cid}")

    tab_info, tab_image, tab_history, tab_actions, tab_spam = st.tabs(
        ["Details", "Image", "History & Escalation", "Actions", "Spam"]
    )

    # -- Details Tab --
    with tab_info:
        col1, col2 = st.columns(2)
        with col1:
            st.write(f"**Status:** {c.get('status')}")
            st.write(f"**Priority:** {c.get('priority')} (score: {c.get('priority_score', 0)})")
            st.write(f"**Visibility:** {c.get('visibility')}")
            st.write(f"**Assigned to:** {c.get('assigned_authority_name', '-')}")
            st.write(f"**Spam flagged:** {c.get('is_marked_as_spam', False)}")
        with col2:
            st.write(f"**Submitted:** {(c.get('submitted_at') or '')[:16]}")
            st.write(f"**Updated:** {(c.get('updated_at') or '')[:16]}")
            if c.get("resolved_at"):
                st.write(f"**Resolved:** {c['resolved_at'][:16]}")
            st.write(f"**Votes:** +{c.get('upvotes', 0)} / -{c.get('downvotes', 0)}")
            if c.get("student_roll_no"):
                st.write(f"**Student:** {c.get('student_name', '?')} ({c['student_roll_no']})")

        st.divider()
        st.subheader("Original Text")
        st.write(c.get("original_text", ""))
        if c.get("rephrased_text"):
            st.subheader("Rephrased Text")
            st.info(c["rephrased_text"])

        if c.get("status_updates"):
            st.subheader("Status Updates")
            for su in c["status_updates"]:
                st.write(
                    f"  {su.get('old_status')} -> **{su.get('new_status')}** "
                    f"| {su.get('reason', '-')} | {(su.get('updated_at') or '')[:16]}"
                )

    # -- Image Tab --
    with tab_image:
        if c.get("has_image"):
            st.write(f"**Filename:** {c.get('image_filename', '-')}")
            st.write(f"**Verification:** {c.get('image_verification_status', '-')}")

            img_resp = api("GET", f"/complaints/{cid}/image")
            if ok(img_resp):
                st.image(img_resp.content, caption="Complaint Image", use_container_width=True)
            else:
                st.warning("Could not load image.")
        else:
            st.info("No image attached.")

    # -- History Tab --
    with tab_history:
        st.subheader("Status History")
        hr = api("GET", f"/complaints/{cid}/status-history")
        if ok(hr):
            hd = hr.json()
            st.write(f"**Current Status:** {hd.get('current_status', '?')}")
            for su in hd.get("status_updates", []):
                st.write(
                    f"  {su.get('old_status')} -> **{su.get('new_status')}** "
                    f"| {su.get('reason', '-')} | by {su.get('updated_by', '?')} "
                    f"| {(su.get('updated_at') or '')[:16]}"
                )
        elif hr is not None:
            show_error(hr)

        st.divider()
        st.subheader("Timeline")
        tr = api("GET", f"/complaints/{cid}/timeline")
        if ok(tr):
            td = tr.json()
            for event in td.get("timeline", []):
                ts = (event.get("timestamp") or "")[:16].replace("T", " ")
                st.write(f"**{event.get('event')}** - {ts}")
                st.caption(event.get("description", ""))
        elif tr is not None:
            show_error(tr)

        st.divider()
        st.subheader("Escalation History")
        er = api("GET", f"/authorities/complaints/{cid}/escalation-history")
        if ok(er):
            ed = er.json()
            st.write(f"**Escalation count:** {ed.get('escalation_count', 0)}")
            for h in ed.get("history", []):
                current = " (CURRENT)" if h.get("is_current") else ""
                st.write(
                    f"  Level {h.get('level', '?')} - **{h.get('authority_name', '?')}** "
                    f"({h.get('authority_type', '?')}){current}"
                )
                if h.get("reason"):
                    st.caption(f"  Reason: {h['reason']}")
        elif er is not None:
            show_error(er)

    # -- Actions Tab --
    with tab_actions:
        current_status = c.get("status", "")
        transitions = VALID_TRANSITIONS.get(current_status, [])

        st.subheader("Update Status")
        if transitions:
            with st.form("update_status"):
                new_status = st.selectbox("New Status", transitions)
                reason = st.text_input("Reason (required for Closed/Spam)")
                submitted = st.form_submit_button("Update Status")
            if submitted:
                body = {"status": new_status}
                if reason.strip():
                    body["reason"] = reason.strip()
                r = api("PUT", f"/authorities/complaints/{cid}/status", json_body=body)
                if ok(r):
                    st.success(r.json().get("message", "Status updated!"))
                    st.rerun()
                else:
                    show_error(r)
        else:
            st.info(f"No transitions available from '{current_status}'.")

        st.divider()

        st.subheader("Post Update")
        with st.form("post_update"):
            pu_title = st.text_input("Title (5-200 chars)")
            pu_content = st.text_area("Content (10-2000 chars)")
            submitted = st.form_submit_button("Post Update")
        if submitted:
            if not pu_title or len(pu_title.strip()) < 5:
                st.warning("Title must be at least 5 characters.")
            elif not pu_content or len(pu_content.strip()) < 10:
                st.warning("Content must be at least 10 characters.")
            else:
                r = api("POST", f"/authorities/complaints/{cid}/post-update",
                        params={"title": pu_title.strip(), "content": pu_content.strip()})
                if ok(r):
                    st.success(r.json().get("message", "Update posted!"))
                    st.rerun()
                else:
                    show_error(r)

        st.divider()

        st.subheader("Escalate Complaint")
        with st.form("escalate"):
            esc_reason = st.text_input("Reason for escalation")
            submitted = st.form_submit_button("Escalate")
        if submitted:
            if not esc_reason.strip():
                st.warning("Reason is required.")
            else:
                r = api("POST", f"/authorities/complaints/{cid}/escalate",
                        params={"reason": esc_reason.strip()})
                if ok(r):
                    st.success(r.json().get("message", "Escalated!"))
                    st.rerun()
                else:
                    show_error(r)

    # -- Spam Tab --
    with tab_spam:
        is_spam = c.get("is_marked_as_spam", False)
        st.write(f"**Currently flagged as spam:** {is_spam}")

        if not is_spam:
            st.subheader("Flag as Spam")
            with st.form("flag_spam"):
                spam_reason = st.text_input("Reason")
                submitted = st.form_submit_button("Flag as Spam")
            if submitted:
                if not spam_reason.strip():
                    st.warning("Reason is required.")
                else:
                    r = api("POST", f"/complaints/{cid}/flag-spam",
                            params={"reason": spam_reason.strip()})
                    if ok(r):
                        st.success(r.json().get("message", "Flagged as spam!"))
                        st.rerun()
                    else:
                        show_error(r)
        else:
            if st.button("Remove Spam Flag"):
                r = api("POST", f"/complaints/{cid}/unflag-spam")
                if ok(r):
                    st.success(r.json().get("message", "Spam flag removed!"))
                    st.rerun()
                else:
                    show_error(r)


# ════════════════════════════════════════════════════════════════
# ADMIN PAGES
# ════════════════════════════════════════════════════════════════

def page_admin_overview():
    st.header("Admin - System Overview")

    resp = api("GET", "/admin/stats/overview")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Students", d.get("total_students", 0))
    c2.metric("Total Authorities", d.get("total_authorities", 0))
    c3.metric("Total Complaints", d.get("total_complaints", 0))
    c4.metric("Recent (7d)", d.get("recent_complaints_7d", 0))

    st.divider()

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Complaints by Status")
        status_data = d.get("complaints_by_status", {})
        if status_data:
            for k, v in status_data.items():
                st.write(f"  **{k}:** {v}")
        else:
            st.caption("No data")

    with col2:
        st.subheader("Complaints by Priority")
        priority_data = d.get("complaints_by_priority", {})
        if priority_data:
            for k, v in priority_data.items():
                st.write(f"  **{k}:** {v}")
        else:
            st.caption("No data")

    st.divider()

    col3, col4 = st.columns(2)
    with col3:
        st.subheader("Complaints by Category")
        cat_data = d.get("complaints_by_category", {})
        if cat_data:
            for k, v in cat_data.items():
                st.write(f"  **{k}:** {v}")
        else:
            st.caption("No data")

    with col4:
        st.subheader("Image Statistics")
        img_data = d.get("image_statistics", {})
        if img_data:
            for k, v in img_data.items():
                st.write(f"  **{k}:** {v}")
        else:
            st.caption("No data")


def page_admin_analytics():
    st.header("Admin - Analytics")

    days = st.slider("Analysis period (days)", min_value=7, max_value=365, value=30)

    resp = api("GET", "/admin/stats/analytics", params={"days": days})
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Total Complaints", d.get("total_complaints", 0))
    c2.metric("Resolved", d.get("resolved_complaints", 0))
    c3.metric("Resolution Rate", f"{d.get('resolution_rate_percent', 0):.1f}%")
    c4.metric("Avg Resolution (hrs)", f"{d.get('avg_resolution_time_hours', 0):.1f}")

    daily = d.get("daily_complaints", [])
    if daily:
        st.divider()
        st.subheader("Daily Complaint Trend")
        import pandas as pd
        df = pd.DataFrame(daily)
        if not df.empty:
            df["date"] = pd.to_datetime(df["date"])
            st.line_chart(df.set_index("date")["count"])


def page_admin_authorities():
    st.header("Admin - Authority Management")

    col1, col2 = st.columns([1, 3])
    filter_active = col1.selectbox("Status", ["All", "Active", "Inactive"], key="auth_filter")

    params = {"skip": 0, "limit": 50}
    if filter_active == "Active":
        params["is_active"] = "true"
    elif filter_active == "Inactive":
        params["is_active"] = "false"

    resp = api("GET", "/admin/authorities", params=params)
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    authorities = d.get("authorities", [])
    total = d.get("total", 0)

    st.caption(f"Total: {total}")

    for i, a in enumerate(authorities):
        cols = st.columns([2, 1.5, 1, 1, 1])
        cols[0].write(f"**{a.get('name')}** ({a.get('email')})")
        cols[1].write(f"{a.get('authority_type')} (Lv {a.get('authority_level')})")
        cols[2].write(f"{'Active' if a.get('is_active') else 'Inactive'}")
        dept = a.get('department_name') or '-'
        cols[3].caption(dept)
        active = a.get('is_active', True)
        btn_label = "Deactivate" if active else "Activate"
        if cols[4].button(btn_label, key=f"auth_toggle_{i}"):
            r = api("PUT", f"/admin/authorities/{a['id']}/toggle-active",
                    params={"activate": str(not active).lower()})
            if ok(r):
                st.success(r.json().get("message", "Done"))
                st.rerun()
            else:
                show_error(r)
        st.divider()

    # Create new authority
    st.divider()
    st.subheader("Create New Authority")
    with st.form("create_authority"):
        ca_name = st.text_input("Name")
        ca_email = st.text_input("Email")
        ca_password = st.text_input("Password", type="password")
        ca_phone = st.text_input("Phone (optional)")
        ca_c1, ca_c2 = st.columns(2)
        authority_types = [
            "Admin", "Admin Officer", "Men's Hostel Warden", "Women's Hostel Warden",
            "Men's Hostel Deputy Warden", "Women's Hostel Deputy Warden",
            "Senior Deputy Warden", "HOD", "Disciplinary Committee",
        ]
        ca_type = ca_c1.selectbox("Authority Type", authority_types)
        ca_level = ca_c2.number_input("Authority Level", min_value=1, max_value=100, value=5)
        ca_dept = st.selectbox("Department (for HOD)", options=[None] + list(DEPARTMENTS.keys()),
                               format_func=lambda x: "None" if x is None else DEPARTMENTS[x])
        ca_designation = st.text_input("Designation (optional)")
        submitted = st.form_submit_button("Create Authority")

    if submitted:
        if not all([ca_name, ca_email, ca_password]):
            st.warning("Name, email and password are required.")
        else:
            body = {
                "name": ca_name.strip(),
                "email": ca_email.strip(),
                "password": ca_password,
                "authority_type": ca_type,
                "authority_level": ca_level,
            }
            if ca_phone and ca_phone.strip():
                body["phone"] = ca_phone.strip()
            if ca_dept is not None:
                body["department_id"] = ca_dept
            if ca_designation and ca_designation.strip():
                body["designation"] = ca_designation.strip()

            r = api("POST", "/admin/authorities", json_body=body)
            if ok(r):
                st.success("Authority created successfully!")
                st.rerun()
            else:
                show_error(r)


def page_admin_students():
    st.header("Admin - Student Management")

    col1, col2, col3 = st.columns([1, 1, 2])
    filter_active = col1.selectbox("Status", ["All", "Active", "Inactive"], key="stu_filter")
    filter_dept = col2.selectbox("Department", [None] + list(DEPARTMENTS.keys()),
                                 format_func=lambda x: "All" if x is None else DEPARTMENTS[x],
                                 key="stu_dept_filter")

    params = {"skip": 0, "limit": 50}
    if filter_active == "Active":
        params["is_active"] = "true"
    elif filter_active == "Inactive":
        params["is_active"] = "false"
    if filter_dept is not None:
        params["department_id"] = filter_dept

    resp = api("GET", "/admin/students", params=params)
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    students = d.get("students", [])
    total = d.get("total", 0)

    st.caption(f"Total: {total}")

    for i, s in enumerate(students):
        cols = st.columns([1.5, 2, 1, 1, 1])
        cols[0].write(f"**{s.get('roll_no')}**")
        cols[1].write(f"{s.get('name')} ({s.get('email')})")
        dept_name = s.get('department_name') or DEPARTMENTS.get(s.get('department_id'), '?')
        cols[2].caption(f"{dept_name} Y{s.get('year', '?')}")
        cols[3].write(f"{'Active' if s.get('is_active') else 'Inactive'}")
        active = s.get('is_active', True)
        btn_label = "Deactivate" if active else "Activate"
        if cols[4].button(btn_label, key=f"stu_toggle_{i}"):
            r = api("PUT", f"/admin/students/{s['roll_no']}/toggle-active",
                    params={"activate": str(not active).lower()})
            if ok(r):
                st.success(r.json().get("message", "Done"))
                st.rerun()
            else:
                show_error(r)
        st.divider()


def page_admin_bulk_ops():
    st.header("Admin - Bulk Operations")

    st.subheader("Bulk Status Update")
    with st.form("bulk_status"):
        complaint_ids_raw = st.text_area(
            "Complaint IDs (one per line)",
            height=100,
            help="Paste complaint UUIDs, one per line"
        )
        new_status = st.selectbox("New Status", STATUSES)
        reason = st.text_input("Reason for bulk update")
        submitted = st.form_submit_button("Apply Bulk Update")

    if submitted:
        if not complaint_ids_raw.strip() or not reason.strip():
            st.warning("Please provide complaint IDs and a reason.")
        else:
            ids = [line.strip() for line in complaint_ids_raw.strip().split("\n") if line.strip()]
            r = api("POST", "/admin/complaints/bulk-status-update",
                    params={
                        "complaint_ids": ids,
                        "new_status": new_status,
                        "reason": reason.strip(),
                    })
            if ok(r):
                st.success(r.json().get("message", "Bulk update complete!"))
            else:
                show_error(r)


def page_admin_image_moderation():
    st.header("Admin - Image Moderation")

    resp = api("GET", "/admin/images/pending-verification")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()
    pending = d.get("pending_images", [])
    total = d.get("total", 0)

    st.caption(f"Pending images: {total}")

    if not pending:
        st.info("No images pending verification.")
        return

    for i, img in enumerate(pending):
        cols = st.columns([2, 1, 1, 1])
        cols[0].write(f"**{img.get('category', '?')}** - {img.get('complaint_text', '')}")
        cols[1].caption(f"File: {img.get('image_filename', '?')} ({img.get('image_size_kb', 0)}KB)")
        cols[2].caption(f"Student: {img.get('student_roll_no', '?')}")

        bc1, bc2 = cols[3].columns(2)
        if bc1.button("Approve", key=f"img_approve_{i}"):
            r = api("POST", f"/admin/images/{img['complaint_id']}/moderate",
                    params={"approve": "true"})
            if ok(r):
                st.success("Image approved!")
                st.rerun()
            else:
                show_error(r)
        if bc2.button("Reject", key=f"img_reject_{i}"):
            r = api("POST", f"/admin/images/{img['complaint_id']}/moderate",
                    params={"approve": "false", "reason": "Rejected by admin"})
            if ok(r):
                st.success("Image rejected!")
                st.rerun()
            else:
                show_error(r)

        # Show image preview
        img_resp = api("GET", f"/complaints/{img['complaint_id']}/image")
        if ok(img_resp):
            st.image(img_resp.content, caption=img.get("image_filename", "Image"), width=300)
        st.divider()


def page_admin_health():
    st.header("Admin - System Health")

    resp = api("GET", "/admin/health/metrics")
    if resp is None:
        st.error("Cannot connect to backend.")
        return
    if not ok(resp):
        show_error(resp)
        return

    d = resp.json()

    c1, c2, c3 = st.columns(3)
    if d.get("database_size_mb") is not None:
        c1.metric("Database Size (MB)", f"{d['database_size_mb']:.2f}")
    c2.metric("Pending Complaints", d.get("pending_complaints", 0))
    c3.metric("Old Unresolved (>7d)", d.get("old_unresolved_7d", 0))

    img_stats = d.get("image_statistics", {})
    if img_stats:
        st.divider()
        st.subheader("Image Statistics")
        for k, v in img_stats.items():
            st.write(f"  **{k}:** {v}")


# ════════════════════════════════════════════════════════════════
# HEALTH CHECK (PUBLIC)
# ════════════════════════════════════════════════════════════════

def page_health():
    st.header("Health Check")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Basic Health")
        r = api("GET", "/health")
        if ok(r):
            st.json(r.json())
        elif r is not None:
            st.error(f"Status {r.status_code}")
        else:
            st.error("Cannot connect to backend.")

    with col2:
        st.subheader("Detailed Health")
        r = api("GET", "/health/detailed")
        if ok(r):
            st.json(r.json())
        elif r is not None:
            st.error(f"Status {r.status_code}")
        else:
            st.error("Cannot connect to backend.")


# ════════════════════════════════════════════════════════════════
# MAIN
# ════════════════════════════════════════════════════════════════

def main():
    st.set_page_config(
        page_title="CampusVoice",
        layout="wide",
        initial_sidebar_state="expanded",
    )
    init_session()

    # -- Not logged in --
    if not st.session_state.token:
        page_auth()
        with st.sidebar:
            st.title("CampusVoice")
            st.caption("Login or register to continue")
            st.divider()
            if st.button("Check Server Health"):
                r = api("GET", "/health")
                if ok(r):
                    st.success("Backend is running!")
                else:
                    st.error("Backend not reachable.")
        return

    # -- Logged in --
    with st.sidebar:
        st.title("CampusVoice")
        user = st.session_state.user or {}
        role = st.session_state.role

        if role == "Student":
            st.write(f"**{user.get('name', '?')}**")
            st.caption(f"Roll: {user.get('roll_no', '?')} | {user.get('department_name', '')}")
        elif role == "Admin":
            st.write(f"**{user.get('name', '?')}**")
            st.caption(f"Admin | {user.get('designation', '')}")
        else:
            st.write(f"**{user.get('name', '?')}**")
            st.caption(f"{user.get('authority_type', '?')} | {user.get('designation', '')}")

        st.divider()

        if role == "Student":
            pages = {
                "Dashboard": page_student_dashboard,
                "Submit Complaint": page_submit_complaint,
                "My Complaints": page_my_complaints,
                "Public Feed": page_public_feed,
                "Advanced Search": page_advanced_search,
                "Notifications": page_notifications,
                "Profile": page_student_profile,
                "Change Password": page_change_password,
                "Health Check": page_health,
            }
        elif role == "Admin":
            pages = {
                "System Overview": page_admin_overview,
                "Analytics": page_admin_analytics,
                "Authority Management": page_admin_authorities,
                "Student Management": page_admin_students,
                "Image Moderation": page_admin_image_moderation,
                "Bulk Operations": page_admin_bulk_ops,
                "System Health": page_admin_health,
                "-- Authority Dashboard": page_authority_dashboard,
                "-- Assigned Complaints": page_authority_complaints,
                "-- Authority Stats": page_authority_stats,
                "-- Authority Profile": page_authority_profile,
                "Health Check": page_health,
            }
        else:
            pages = {
                "Dashboard": page_authority_dashboard,
                "Assigned Complaints": page_authority_complaints,
                "Statistics": page_authority_stats,
                "Profile": page_authority_profile,
                "Health Check": page_health,
            }

        choice = st.radio("Navigate", list(pages.keys()))

        st.divider()
        if st.button("Logout"):
            logout()

    # -- Render page --
    if st.session_state.selected_complaint:
        if role == "Student":
            page_complaint_detail_student()
        else:
            page_complaint_detail_authority()
    else:
        pages[choice]()


if __name__ == "__main__":
    main()
