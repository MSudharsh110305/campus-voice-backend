import httpx
from tkinter import Tk, filedialog
import getpass
import json

BASE_URL = "http://localhost:8000"
TIMEOUT = 30.0

session = {"token": None, "role": None, "email": None}


def select_file(title="Select a file"):
    root = Tk()
    root.withdraw()
    root.attributes("-topmost", True)
    path = filedialog.askopenfilename(title=title)
    root.destroy()
    return path


def show_resp(resp):
    print(f"HTTP {resp.status_code}")
    try:
        print(json.dumps(resp.json(), indent=2))
    except Exception:
        print(resp.text)


def api_post(path, json_body=None, files=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.post(f"{BASE_URL}{path}", json=json_body, files=files, headers=headers)


def api_get(path, params=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.get(f"{BASE_URL}{path}", params=params, headers=headers)


def api_put(path, json_body=None, token=None):
    headers = {}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    with httpx.Client(timeout=TIMEOUT) as client:
        return client.put(f"{BASE_URL}{path}", json=json_body, headers=headers)


def register():
    payload = {
        "roll_no": input("Roll No: ").strip(),
        "name": input("Name: ").strip(),
        "email": input("Email: ").strip(),
        "password": getpass.getpass("Password: ").strip(),
        "gender": input("Gender: ").strip(),
        "stay_type": input("Stay Type (Hostel/Day Scholar): ").strip(),
        "year": input("Year (1st Year/...): ").strip(),
        "department_id": input("Department code (CSE/ECE/...): ").strip(),
    }
    resp = api_post("/api/students/register", json_body=payload)
    show_resp(resp)


def login_student():
    identifier = input("Email or Roll No: ").strip()
    password = getpass.getpass("Password: ").strip()
    resp = api_post("/api/students/login", json_body={"email_or_roll_no": identifier, "password": password})
    show_resp(resp)
    if resp.status_code == 200:
        data = resp.json()
        session.update({"token": data.get("token"), "role": "student", "email": data.get("email")})


def submit_complaint():
    if not session.get("token"):
        print("Login required")
        return
    text = input("Complaint text: ").strip()
    visibility = input("Visibility (Private/Department/Public) [Public]: ").strip() or "Public"
    resp = api_post("/api/complaints/submit", json_body={"original_text": text, "visibility": visibility}, token=session["token"])
    show_resp(resp)


def view_my_complaints():
    if not session.get("token"):
        print("Login required")
        return
    resp = api_get("/api/students/my-complaints", token=session["token"])
    show_resp(resp)


def view_public_feed():
    if not session.get("token"):
        print("Login required")
        return
    stay = input("Filter stay_type (Hostel/Day Scholar) or Enter to skip: ").strip() or None
    dept = input("Filter department code or Enter to skip: ").strip() or None
    params = {}
    if stay:
        params["stay_type"] = stay
    if dept:
        params["department"] = dept
    resp = api_get("/api/complaints/public-feed", params=params, token=session["token"])
    show_resp(resp)


def vote():
    if not session.get("token"):
        print("Login required")
        return
    cid = input("Complaint ID: ").strip()
    vt = input("Vote (Upvote/Downvote): ").strip()
    resp = api_post(f"/api/complaints/{cid}/vote", json_body={"vote_type": vt}, token=session["token"])
    show_resp(resp)


def upload_image():
    if not session.get("token"):
        print("Login required")
        return
    cid = input("Complaint ID: ").strip()
    path = select_file("Select image file")
    if not path:
        print("No file selected")
        return
    with open(path, "rb") as f:
        files = {"file": (path.split("/")[-1], f, "image/jpeg")}
        headers = {"Authorization": f"Bearer {session['token']}"} if session.get("token") else {}
        with httpx.Client(timeout=TIMEOUT) as client:
            resp = client.post(f"{BASE_URL}/api/complaints/{cid}/upload-image", files=files, headers=headers)
    show_resp(resp)


def login_authority():
    email = input("Authority Email: ").strip()
    password = getpass.getpass("Password: ").strip()
    resp = api_post("/api/authorities/login", json_body={"email": email, "password": password})
    show_resp(resp)
    if resp.status_code == 200:
        session.update({"token": resp.json().get("token"), "role": "authority", "email": email})


def view_assigned():
    if not session.get("token"):
        print("Login required")
        return
    resp = api_get("/api/authorities/my-complaints", token=session["token"])
    show_resp(resp)


def update_status():
    if not session.get("token"):
        print("Login required")
        return
    cid = input("Complaint ID: ").strip()
    status = input("New status: ").strip()
    reason = input("Reason (optional): ").strip()
    resp = api_put(f"/api/authorities/complaints/{cid}/status", json_body={"status": status, "reason": reason}, token=session["token"])
    show_resp(resp)


def logout():
    session.clear()
    print("Logged out")


def menu():
    while True:
        print("""
1) Student Register
2) Student Login
3) Submit Complaint
4) View My Complaints
5) View Public Feed
6) Vote
7) Upload Image
8) Authority Login
9) View Assigned Complaints
10) Update Complaint Status
11) Logout
0) Exit
""")
        c = input("Choose: ").strip()
        if c == "1":
            register()
        elif c == "2":
            login_student()
        elif c == "3":
            submit_complaint()
        elif c == "4":
            view_my_complaints()
        elif c == "5":
            view_public_feed()
        elif c == "6":
            vote()
        elif c == "7":
            upload_image()
        elif c == "8":
            login_authority()
        elif c == "9":
            view_assigned()
        elif c == "10":
            update_status()
        elif c == "11":
            logout()
        elif c == "0":
            break
        else:
            print("Invalid choice")


if __name__ == "__main__":
    print("Client will talk to", BASE_URL)
    menu()
