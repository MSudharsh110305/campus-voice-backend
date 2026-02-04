"""
Automated client test script.

- Creates 10 students (mixed departments & stay types)
- Registers + logs each in
- Each student submits a complaint
- Uploads an image for each complaint (prompts for an image file once; if none chosen, uses generated images)
- Shows a chosen student's "my complaints"
- Fetches public feed (prints)
- Performs voting on a target complaint and shows real-time vote counts
- Logs in as authority, views assigned complaints, updates status of target complaint
- Attempts to post an authority update (if endpoint exists) and reports result

Run while backend is running: python client_test.py
"""

import httpx
import json
import random
import time
import sys
from tkinter import Tk, filedialog
from io import BytesIO
from PIL import Image

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

DEPARTMENTS = ["CSE", "ECE", "MECH", "CIVIL", "IT"]
STAY_TYPES = ["Hostel", "Day Scholar"]


def pretty_print_resp(resp: httpx.Response, note: str = ""):
    """
    Print HTTP response in readable JSON form.
    Handles None responses gracefully.
    """
    if resp is None:
        prefix = f"[NO RESPONSE] {note}" if note else "[NO RESPONSE]"
        print(prefix)
        print("No response (request may have failed).")
        print("-" * 80)
        return

    prefix = f"[{resp.status_code}] {note}" if note else f"[{resp.status_code}]"
    print(prefix)
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)
    print("-" * 80)


def select_image_once():
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title="Select an image file to use for uploads (Cancel to auto-generate)")
    root.destroy()
    return path or None


def generate_image_bytes(color=(200, 100, 100), size=(300, 200)):
    img = Image.new("RGB", size, color=color)
    buf = BytesIO()
    img.save(buf, format="JPEG")
    buf.seek(0)
    return buf


def register_student(client: httpx.Client, student):
    try:
        resp = client.post(f"{BASE_URL}/api/students/register", json=student, timeout=TIMEOUT)
    except Exception as e:
        print("Register request error:", e)
        return None
    pretty_print_resp(resp, f"Register {student['email']}")
    return resp


def login_student(client: httpx.Client, identifier, password):
    try:
        resp = client.post(f"{BASE_URL}/api/students/login", json={"email_or_roll_no": identifier, "password": password}, timeout=TIMEOUT)
    except Exception as e:
        print("Login request error:", e)
        return None
    pretty_print_resp(resp, f"Login {identifier}")
    if resp.status_code == 200:
        return resp.json().get("token")
    return None


def submit_complaint(client: httpx.Client, token: str, text: str, visibility: str = "Public"):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.post(f"{BASE_URL}/api/complaints/submit", json={"original_text": text, "visibility": visibility}, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print("Submit complaint error:", e)
        return None
    pretty_print_resp(resp, f"Submit complaint")
    if resp.status_code == 201:
        return resp.json().get("complaint_id")
    return None


def upload_image(client: httpx.Client, token: str, complaint_id: str, file_tuple):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        # httpx expects files as dict: {'file': (filename, fileobj, content_type)}
        resp = client.post(f"{BASE_URL}/api/complaints/{complaint_id}/upload-image", files={"file": file_tuple}, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print("Upload image error:", e)
        return None
    pretty_print_resp(resp, f"Upload image for {complaint_id}")
    return resp


def view_my_complaints(client: httpx.Client, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.get(f"{BASE_URL}/api/students/my-complaints", headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print("My complaints error:", e)
        return None
    pretty_print_resp(resp, "My complaints")
    return resp


def public_feed(client: httpx.Client, token: str, params=None):
    headers = {"Authorization": f"Bearer {token}"} if token else {}
    try:
        resp = client.get(f"{BASE_URL}/api/complaints/public-feed", headers=headers, params=params, timeout=TIMEOUT)
    except Exception as e:
        print("Public feed error:", e)
        return None
    pretty_print_resp(resp, f"Public feed params={params}")
    return resp


def vote_complaint(client: httpx.Client, token: str, complaint_id: str, vote_type: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.post(f"{BASE_URL}/api/complaints/{complaint_id}/vote", json={"vote_type": vote_type}, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print("Vote error:", e)
        return None
    pretty_print_resp(resp, f"Vote {vote_type} on {complaint_id}")
    return resp


def login_authority(client: httpx.Client, email: str, password: str):
    try:
        resp = client.post(f"{BASE_URL}/api/authorities/login", json={"email": email, "password": password}, timeout=TIMEOUT)
    except Exception as e:
        print("Authority login error:", e)
        return None
    pretty_print_resp(resp, f"Authority login {email}")
    if resp.status_code == 200:
        return resp.json().get("token")
    return None


def view_assigned(client: httpx.Client, token: str):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.get(f"{BASE_URL}/api/authorities/my-complaints", headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print("View assigned error:", e)
        return None
    pretty_print_resp(resp, "Authority assigned complaints")
    return resp


def update_status(client: httpx.Client, token: str, complaint_id: str, status: str, reason: str = ""):
    headers = {"Authorization": f"Bearer {token}"}
    try:
        resp = client.put(f"{BASE_URL}/api/authorities/complaints/{complaint_id}/status", json={"status": status, "reason": reason}, headers=headers, timeout=TIMEOUT)
    except Exception as e:
        print("Update status error:", e)
        return None
    pretty_print_resp(resp, f"Update status {complaint_id} -> {status}")
    return resp


def try_post_update(client: httpx.Client, token: str, complaint_id: str, update_text: str, is_public: bool = True):
    """Try common possible endpoints for posting an authority update; print result(s)."""
    headers = {"Authorization": f"Bearer {token}"}
    endpoints = [
        f"/api/authorities/complaints/{complaint_id}/post-update",
        f"/api/authorities/complaints/{complaint_id}/updates",
        f"/api/authorities/complaints/{complaint_id}/announcement",
    ]
    for ep in endpoints:
        try:
            resp = client.post(f"{BASE_URL}{ep}", json={"update_text": update_text, "is_public": is_public}, headers=headers, timeout=TIMEOUT)
            pretty_print_resp(resp, f"POST {ep}")
        except Exception as e:
            print(f"POST {ep} error:", e)


# Open a log file and tee stdout/stderr so all output is saved for reference
_log_path = "client_test_output.txt"
_log_file = open(_log_path, "w", encoding="utf-8")

class _Tee:
    def __init__(self, orig, file):
        self.orig = orig
        self.file = file
    def write(self, s):
        try:
            self.orig.write(s)
        except Exception:
            pass
        try:
            self.file.write(s)
        except Exception:
            pass
    def flush(self):
        try:
            self.orig.flush()
        except Exception:
            pass
        try:
            self.file.flush()
        except Exception:
            pass

# replace global stdout/stderr
sys.stdout = _Tee(sys.stdout, _log_file)
sys.stderr = _Tee(sys.stderr, _log_file)


def main():
    client = httpx.Client(timeout=TIMEOUT)
    # 1) create 10 students
    students = []
    for i in range(1, 11):
        s = {
            "roll_no": f"23CS{100+i}",
            "name": f"Student{i}",
            "email": f"student{i}@college.edu",
            "password": "Pass@1234",
            "gender": "Other" if i % 3 == 0 else ("Male" if i % 2 == 0 else "Female"),
            "stay_type": random.choice(STAY_TYPES),
            "year": f"{(i%4)+1}st Year" if (i%4)+1 == 1 else f"{(i%4)+1}nd Year" if (i%4)+1==2 else f"{(i%4)+1}rd Year" if (i%4)+1==3 else f"{(i%4)+1}th Year",
            "department_id": random.choice(DEPARTMENTS)
        }
        # normalize year strings to match VALID_YEARS pattern used by backend (simple mapping)
        year_map = {1: "1st Year", 2: "2nd Year", 3: "3rd Year", 4: "4th Year"}
        ynum = ((i - 1) % 4) + 1
        s["year"] = year_map[ynum]
        students.append(s)

    print("Select an image file to use for uploads (or Cancel to auto-generate images)")
    chosen_path = select_image_once()

    tokens = {}
    complaint_ids = {}

    print("Registering students...")
    for s in students:
        resp = register_student(client, s)
        if resp is None or resp.status_code != 201:
            # try login if exists
            pass
        # login to obtain token
        token = login_student(client, s["email"], s["password"])
        if token:
            tokens[s["email"]] = token
        else:
            print(f"Failed to log in {s['email']}")

    # submit complaints
    print("Submitting complaints for each student...")
    for idx, s in enumerate(students, start=1):
        token = tokens.get(s["email"])
        if not token:
            print("Skipping submit for", s["email"])
            continue
        text = f"{s['name']} reports issue for {s['department_id']}: example problem #{idx}"
        cid = submit_complaint(client, token, text, visibility="Public")
        if cid:
            complaint_ids[s["email"]] = cid

            # upload image: use chosen_path if available, otherwise generate
            if chosen_path:
                try:
                    with open(chosen_path, "rb") as f:
                        file_tuple = (chosen_path.split("/")[-1], f, "image/jpeg")
                        # httpx will read file; need to re-open for each upload so we pass an actual file object
                        resp = upload_image(client, token, cid, file_tuple)
                except Exception as e:
                    print("File upload failed (will generate):", e)
                    buf = generate_image_bytes(color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
                    file_tuple = (f"auto_{idx}.jpg", buf, "image/jpeg")
                    upload_image(client, token, cid, file_tuple)
            else:
                buf = generate_image_bytes(color=(random.randint(0,255), random.randint(0,255), random.randint(0,255)))
                file_tuple = (f"auto_{idx}.jpg", buf, "image/jpeg")
                upload_image(client, token, cid, file_tuple)

    # pick target user (student1)
    target_email = students[0]["email"]
    target_cid = complaint_ids.get(target_email)
    if not target_cid:
        print("No target complaint found; aborting voting/status flow")
        return

    # view target student's complaints
    print(f"Viewing complaints for {target_email}")
    view_my_complaints(client, tokens[target_email])

    # view public feed
    print("Public feed (initial)")
    public_feed(client, tokens[target_email])

    # voting: use students 2..6 to vote on target complaint
    voters = [students[i]["email"] for i in range(1, 6) if students[i]["email"] in tokens]
    for v_email in voters:
        vt = random.choice(["Upvote", "Downvote"])
        print(f"{v_email} voting {vt} on {target_cid}")
        vote_complaint(client, tokens[v_email], target_cid, vt)
        # fetch public feed to show real-time reflection
        public_feed(client, tokens[v_email])
        time.sleep(0.2)

    # login as authority and view assigned complaints
    print("Authority login as warden@college.edu")
    auth_token = login_authority(client, "warden@college.edu", "Warden@123")
    if auth_token:
        view_assigned(client, auth_token)

        # change status of target complaint
        print(f"Authority updating status of {target_cid} to 'In Progress'")
        update_status(client, auth_token, target_cid, "In Progress", reason="Investigating")

        # attempt to post a public update (may not be implemented)
        print("Attempting to post authority update for the complaint (if endpoint exists)")
        try_post_update(client, auth_token, target_cid, "We are looking into this issue. Expected resolution in 48 hours.", is_public=True)

    # as target student, verify status changed and (if update posted) see updates
    print(f"Target student ({target_email}) fetching my complaints to verify status/update visibility")
    view_my_complaints(client, tokens[target_email])

    # verify other students cannot see private updates — attempt by a different student
    other_email = students[2]["email"]
    print(f"Another student ({other_email}) fetching public feed (should not see private-only updates)")
    public_feed(client, tokens[other_email])

    print("Client test complete.")

    # Cleanup in-memory backend (testing only)
    try:
        resp = client.post(f"{BASE_URL}/testing/cleanup", timeout=TIMEOUT)
        pretty_print_resp(resp, "Testing cleanup")
    except Exception as e:
        print("Cleanup request failed:", e)

    client.close()

    # close the log file (restore stdout/stderr if desired)
    try:
        _log_file.flush()
        _log_file.close()
    except Exception:
        pass


if __name__ == "__main__":
    main()
