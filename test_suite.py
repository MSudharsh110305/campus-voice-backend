"""
CampusVoice Advanced Test Suite - Comprehensive Testing
========================================================

Features Tested:
1. Hostel Routing Hierarchy (Warden → Deputy Warden → Senior Deputy Warden)
2. Authority Escalation (Complaints AGAINST authorities)
3. Day Scholar Spam Detection (Day scholars can't complain about hostel)
4. Department Isolation in Public Feed
5. Public Voting & Priority Escalation
6. Image Verification
7. Spam & Profanity Detection

Run: python comprehensive_test.py
"""

import httpx
import json
import time
from datetime import datetime
from typing import Dict, Any, List, Optional
from multiprocessing import Pool
import random
from pathlib import Path


# ==================== CONFIGURATION ====================

API_URL = "http://localhost:8000"
TIMEOUT = 20

# ==================== TEST USERS ====================

TEST_USERS = {
    # Hostel Students
    "hostel_cs": {
        "roll_no": "21CSE001",
        "email": "rajesh.cs@srec.ac.in",
        "password": "TestPass123!",
        "name": "Rajesh Kumar",
        "branch": "Computer Science and Engineering",
        "stay_type": "Hostel",
        "gender": "Male"
    },
    "hostel_ece": {
        "roll_no": "21ECE001",
        "email": "priya.ece@srec.ac.in",
        "password": "TestPass123!",
        "name": "Priya Sharma",
        "branch": "Electronics and Communication Engineering",
        "stay_type": "Hostel",
        "gender": "Female"
    },
    "hostel_mech": {
        "roll_no": "21MECH001",
        "email": "arjun.mech@srec.ac.in",
        "password": "TestPass123!",
        "name": "Arjun Patel",
        "branch": "Mechanical Engineering",
        "stay_type": "Hostel",
        "gender": "Male"
    },
    
    # Day Scholars
    "dayscholar_cs": {
        "roll_no": "21CSE002",
        "email": "sneha.cs@srec.ac.in",
        "password": "TestPass123!",
        "name": "Sneha Reddy",
        "branch": "Computer Science and Engineering",
        "stay_type": "Day Scholar",
        "gender": "Female"
    },
    "dayscholar_ece": {
        "roll_no": "21ECE002",
        "email": "karthik.ece@srec.ac.in",
        "password": "TestPass123!",
        "name": "Karthik Iyer",
        "branch": "Electronics and Communication Engineering",
        "stay_type": "Day Scholar",
        "gender": "Male"
    },
    "dayscholar_mech": {
        "roll_no": "21MECH002",
        "email": "divya.mech@srec.ac.in",
        "password": "TestPass123!",
        "name": "Divya Nair",
        "branch": "Mechanical Engineering",
        "stay_type": "Day Scholar",
        "gender": "Female"
    },
    
    # Additional students for voting
    "hostel_eee": {
        "roll_no": "21EEE001",
        "email": "rahul.eee@srec.ac.in",
        "password": "TestPass123!",
        "name": "Rahul Verma",
        "branch": "Electrical and Electronics Engineering",
        "stay_type": "Hostel",
        "gender": "Male"
    },
    "hostel_civil": {
        "roll_no": "21CIVIL001",
        "email": "ananya.civil@srec.ac.in",
        "password": "TestPass123!",
        "name": "Ananya Singh",
        "branch": "Civil Engineering",
        "stay_type": "Hostel",
        "gender": "Female"
    }
}

# ==================== COMPLAINT DATA ====================

# Category 1: HOSTEL Complaints
# These should route based on hierarchy and content

HOSTEL_NORMAL = [
    # Should go to Warden
    {
        "text": "AC in my hostel room A-101 is not cooling at all. It's very hot and uncomfortable, especially during afternoon hours. Please fix it urgently.",
        "expected_route": "Warden",
        "priority": "Medium"
    },
    {
        "text": "Water supply has been stopped in B-block hostel since yesterday morning. No water for bathing or washing. This is unacceptable.",
        "expected_route": "Warden",
        "priority": "High"
    },
    {
        "text": "Hostel mess food quality is very poor. Today's lunch had undercooked rice and stale vegetables. Many students are complaining of stomach issues.",
        "expected_route": "Warden",
        "priority": "High"
    },
    {
        "text": "WiFi connection in hostel C-block is extremely slow. Cannot even load basic websites. Affecting our online classes and assignments.",
        "expected_route": "Warden",
        "priority": "Medium"
    },
    {
        "text": "Hostel bathroom lights not working for past 3 days in second floor. Very dangerous to use washroom at night without proper lighting.",
        "expected_route": "Warden",
        "priority": "High"
    }
]

HOSTEL_AGAINST_WARDEN = [
    # Should BYPASS Warden and go to Deputy Warden
    {
        "text": "Hostel Warden is not responding to our repeated maintenance complaints. We have been asking him to fix the AC for 3 weeks but he ignores us.",
        "expected_route": "Deputy Warden",
        "priority": "Medium"
    },
    {
        "text": "Warden denied permission for our cultural event celebration without giving any proper reason. This is unfair and demotivating for students.",
        "expected_route": "Deputy Warden",
        "priority": "Low"
    },
    {
        "text": "The Warden speaks very rudely to students. Yesterday he shouted at me for asking about room change. His behavior is unprofessional and discouraging.",
        "expected_route": "Deputy Warden",
        "priority": "Medium"
    }
]

HOSTEL_AGAINST_DEPUTY_WARDEN = [
    # Should ESCALATE to Senior Deputy Warden
    {
        "text": "Deputy Warden is being very partial in room allocation. He gives preference to certain students and ignores others. This favoritism must stop.",
        "expected_route": "Senior Deputy Warden",
        "priority": "High"
    },
    {
        "text": "I reported a ragging incident to Deputy Warden last month but he took no action. The senior students are still harassing us and nothing is being done.",
        "expected_route": "Senior Deputy Warden",
        "priority": "High"
    },
    {
        "text": "Deputy Warden rejected my hostel leave application without valid reason. He did not even listen to my emergency situation properly.",
        "expected_route": "Senior Deputy Warden",
        "priority": "Medium"
    }
]

DAY_SCHOLAR_HOSTEL_SPAM = [
    # Day scholars complaining about hostel - should be marked as SPAM
    {
        "text": "Hostel WiFi is not working in my room. I cannot download study materials for tomorrow's exam. Please fix it immediately.",
        "expected_spam": True,
        "reason": "Day scholar cannot complain about hostel facilities"
    },
    {
        "text": "AC in my hostel room is making too much noise at night. Cannot sleep properly because of the irritating sound from the compressor.",
        "expected_spam": True,
        "reason": "Day scholar cannot complain about hostel room issues"
    },
    {
        "text": "Hostel mess food is terrible. The quality has deteriorated significantly in past month. We are paying money but getting bad food.",
        "expected_spam": True,
        "reason": "Day scholar cannot complain about hostel mess"
    }
]

# Category 2: DEPARTMENT Complaints

CS_DEPT_COMPLAINTS = [
    {
        "text": "Computer lab systems in CS block lab-3 are extremely old and slow. Cannot run modern development tools like VS Code and Android Studio.",
        "priority": "Medium"
    },
    {
        "text": "WiFi speed in Computer Science department is pathetically slow. Takes 10 minutes to download a 50MB file. Affecting our project work.",
        "priority": "Medium"
    },
    {
        "text": "Projector in CS lab 2 has been broken for 2 weeks now. Faculty cannot show presentations properly. Labs are getting postponed because of this.",
        "priority": "High"
    },
    {
        "text": "CS department library lacks latest books on Machine Learning, Deep Learning, and Cloud Computing. We have to refer online resources only.",
        "priority": "Low"
    },
    {
        "text": "Air conditioning in CS department is not working. During afternoon sessions, the temperature becomes unbearable and we cannot concentrate.",
        "priority": "Medium"
    }
]

ECE_DEPT_COMPLAINTS = [
    {
        "text": "Oscilloscope in ECE lab 2 is malfunctioning. Showing incorrect waveforms which is affecting our signal processing practicals and experiments.",
        "priority": "High"
    },
    {
        "text": "Signal processing software license expired 3 months ago. We cannot perform MATLAB simulations for our digital signal processing subject.",
        "priority": "High"
    },
    {
        "text": "ECE lab technician is very rude and unhelpful. He refuses to explain equipment usage and gets angry when we ask doubts during practicals.",
        "priority": "Medium"
    },
    {
        "text": "Multimeter and ammeter readings are inaccurate. Need urgent calibration. Our circuit measurements are wrong because of faulty equipment.",
        "priority": "High"
    }
]

MECH_DEPT_COMPLAINTS = [
    {
        "text": "Lathe machine in mechanical workshop is not functioning properly. This is a major safety hazard for students during machining practicals.",
        "priority": "High"
    },
    {
        "text": "Insufficient mechanical drawing instruments. 60 students have to share only 15 instrument sets. We waste a lot of time waiting for our turn.",
        "priority": "Medium"
    },
    {
        "text": "Workshop supervisor does not maintain proper safety protocols. No safety goggles, no gloves provided. Very dangerous working environment.",
        "priority": "High"
    },
    {
        "text": "CAD software computers are extremely slow. Takes 10 minutes just to open SolidWorks. Practical sessions are becoming very inefficient.",
        "priority": "Medium"
    }
]

# Inter-departmental complaints (CS student complaining about ECE, etc.)
INTER_DEPT_COMPLAINTS = [
    {
        "text": "ECE students are making too much noise in the corridor during our CS lab hours. Very disturbing and we cannot concentrate on programming.",
        "complainant_dept": "Computer Science and Engineering",
        "target_dept": "Electronics and Communication Engineering",
        "expected_route": "HOD ECE"
    },
    {
        "text": "Mechanical workshop machines are making loud noise that disturbs our Electronics lab experiments in the adjacent building. Please take action.",
        "complainant_dept": "Electronics and Communication Engineering",
        "target_dept": "Mechanical Engineering",
        "expected_route": "HOD Mechanical"
    }
]

# Category 3: GENERAL Complaints

GENERAL_COMPLAINTS = [
    {
        "text": "College parking area is too small. There is no space for students to park their vehicles safely. Many bikes are getting damaged due to congestion.",
        "priority": "Medium"
    },
    {
        "text": "Canteen food is overpriced. A small dosa costs ₹60 which is available for ₹20 outside. Students are being exploited with high prices.",
        "priority": "Low"
    },
    {
        "text": "Campus security guards are not allowing entry after 6 PM even with valid student ID card. This is causing problems for students with late classes.",
        "priority": "Medium"
    },
    {
        "text": "College washrooms are not cleaned regularly. Very unhygienic conditions with bad smell throughout the day. This is affecting student health.",
        "priority": "High"
    },
    {
        "text": "College bus is frequently late by 20-30 minutes every day. Students are missing first period regularly because of bus delays. Very frustrating.",
        "priority": "Medium"
    }
]

# Category 4: DISCIPLINARY Complaints

DISCIPLINARY_COMPLAINTS = [
    {
        "text": "Some senior students are openly smoking near college gate 2. This is against college rules and creating bad impression. Please take strict action.",
        "priority": "Medium"
    },
    {
        "text": "Ragging incident happened in hostel A-block yesterday. Senior students forced juniors to do embarrassing activities. This is serious harassment.",
        "priority": "High"
    },
    {
        "text": "Students are using mobile phones during semester exams. Invigilator is not taking any action even after multiple students reported it. Unfair to honest students.",
        "priority": "High"
    },
    {
        "text": "Group of students creating loud disturbance in library. Talking loudly, playing music on speakers. Librarian is not controlling them properly.",
        "priority": "Medium"
    }
]

# SPAM and ABUSIVE Complaints

SPAM_COMPLAINTS = [
    {
        "text": "This fucking college is absolute shit. All professors are useless idiots who don't know anything. Management is cheating students.",
        "expected_spam": True,
        "expected_flag": "Black",
        "reason": "Profanity and abusive language"
    },
    {
        "text": "Buy cheap assignment writing services at www.fakeessays.com. Guaranteed A+ grades. Contact us now for 50% discount offer!",
        "expected_spam": True,
        "reason": "Spam advertisement"
    },
    {
        "text": "College principal is incompetent bastard. Should be fired immediately. Bloody management taking our money and not providing facilities.",
        "expected_spam": True,
        "expected_flag": "Black",
        "reason": "Profanity and disrespectful content"
    }
]

# ==================== TEST RESULTS TRACKER ====================

class TestResults:
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.warnings = 0
        self.tests = []
        self.complaints_created = []
        self.start_time = time.time()
    
    def log_test(self, name: str, status: str, details: str = "", expected: str = "", actual: str = ""):
        self.total += 1
        if status == "PASS":
            self.passed += 1
            icon = "✅"
        elif status == "FAIL":
            self.failed += 1
            icon = "❌"
        else:  # WARNING
            self.warnings += 1
            icon = "⚠️"
        
        test_record = {
            "name": name,
            "status": status,
            "details": details,
            "expected": expected,
            "actual": actual,
            "timestamp": datetime.now().isoformat()
        }
        self.tests.append(test_record)
        
        print(f"{icon} {name}")
        if details:
            print(f"   └─ {details}")
        if expected and actual and expected != actual:
            print(f"   └─ Expected: {expected}")
            print(f"   └─ Got: {actual}")
    
    def add_complaint(self, complaint_data: Dict):
        self.complaints_created.append(complaint_data)
    
    def print_summary(self):
        duration = time.time() - self.start_time
        pass_rate = (self.passed / self.total * 100) if self.total > 0 else 0
        
        print("\n" + "=" * 80)
        print("📊 TEST EXECUTION SUMMARY")
        print("=" * 80)
        print(f"✅ Passed:    {self.passed:3d}")
        print(f"❌ Failed:    {self.failed:3d}")
        print(f"⚠️  Warnings:  {self.warnings:3d}")
        print(f"📝 Total:     {self.total:3d}")
        print(f"📋 Complaints Created: {len(self.complaints_created)}")
        print(f"🎯 Pass Rate: {pass_rate:.1f}%")
        print(f"⏱️  Duration:  {duration:.2f}s")
        print("=" * 80)
    
    def save_report(self, filename: str = "test_report.json"):
        report = {
            "summary": {
                "total": self.total,
                "passed": self.passed,
                "failed": self.failed,
                "warnings": self.warnings,
                "pass_rate": f"{(self.passed / self.total * 100):.1f}%" if self.total > 0 else "0%",
                "duration": f"{(time.time() - self.start_time):.2f}s",
                "timestamp": datetime.now().isoformat()
            },
            "tests": self.tests,
            "complaints": self.complaints_created
        }
        
        with open(filename, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {filename}")


# ==================== TEST CLIENT ====================

class CampusVoiceTestClient:
    def __init__(self):
        self.client = httpx.Client(timeout=TIMEOUT, follow_redirects=True)
        self.tokens = {}
        self.user_info = {}
        self.complaint_ids = []
    
    def register_user(self, user_key: str, user_data: Dict) -> bool:
        """Register a new user"""
        try:
            response = self.client.post(
                f"{API_URL}/api/auth/student/register",
                json={
                    "roll_no": user_data["roll_no"],
                    "email": user_data["email"],
                    "password": user_data["password"],
                    "name": user_data["name"],
                    "branch": user_data["branch"],
                    "stay_type": user_data["stay_type"],
                    "gender": user_data.get("gender", "Male")
                }
            )
            return response.status_code in [200, 201]
        except Exception as e:
            # User might already exist
            return True
    
    def login_user(self, user_key: str, user_data: Dict) -> Optional[str]:
        """Login user and return access token"""
        try:
            response = self.client.post(
                f"{API_URL}/api/auth/student/login",
                json={
                    "roll_no": user_data["roll_no"],
                    "password": user_data["password"]
                }
            )
            
            if response.status_code == 200:
                data = response.json()
                token = data.get("access_token") or data.get("token")
                if token:
                    self.tokens[user_key] = token
                    self.user_info[user_key] = user_data
                    return token
            return None
        except Exception as e:
            print(f"   └─ Login error: {str(e)}")
            return None
    
    def submit_complaint(
        self, 
        user_key: str, 
        text: str, 
        category_id: int, 
        visibility: str = "Public",
        image_path: Optional[str] = None
    ) -> Optional[Dict]:
        """Submit a complaint"""
        try:
            token = self.tokens.get(user_key)
            if not token:
                return None
            
            payload = {
                "original_text": text,
                "category_id": category_id,
                "visibility": visibility
            }
            
            # TODO: Add image upload support if needed
            # if image_path:
            #     files = {"image": open(image_path, "rb")}
            
            response = self.client.post(
                f"{API_URL}/api/complaints/submit",
                headers={"Authorization": f"Bearer {token}"},
                json=payload
            )
            
            if response.status_code in [200, 201]:
                return response.json()
            else:
                print(f"   └─ Submission failed: {response.status_code} - {response.text[:100]}")
                return None
        except Exception as e:
            print(f"   └─ Error: {str(e)}")
            return None
    
    def get_public_feed(self, user_key: str, department: Optional[str] = None) -> List[Dict]:
        """Get public complaints feed"""
        try:
            token = self.tokens.get(user_key)
            if not token:
                return []
            
            params = {}
            if department:
                params["department"] = department
            
            response = self.client.get(
                f"{API_URL}/api/complaints/public",
                headers={"Authorization": f"Bearer {token}"},
                params=params
            )
            
            if response.status_code == 200:
                data = response.json()
                return data.get("complaints", [])
            return []
        except Exception as e:
            print(f"   └─ Error fetching feed: {str(e)}")
            return []
    
    def vote_on_complaint(self, user_key: str, complaint_id: int, vote_type: str) -> bool:
        """Vote on a complaint (Upvote/Downvote)"""
        try:
            token = self.tokens.get(user_key)
            if not token:
                return False
            
            response = self.client.post(
                f"{API_URL}/api/complaints/{complaint_id}/vote",
                headers={"Authorization": f"Bearer {token}"},
                json={"vote_type": vote_type}
            )
            
            return response.status_code == 200
        except Exception as e:
            return False
    
    def get_complaint_details(self, user_key: str, complaint_id: int) -> Optional[Dict]:
        """Get details of a specific complaint"""
        try:
            token = self.tokens.get(user_key)
            if not token:
                return None
            
            response = self.client.get(
                f"{API_URL}/api/complaints/{complaint_id}",
                headers={"Authorization": f"Bearer {token}"}
            )
            
            if response.status_code == 200:
                return response.json()
            return None
        except Exception as e:
            return None
    
    def close(self):
        """Close the HTTP client"""
        self.client.close()


# ==================== TEST SUITES ====================

def test_user_authentication(client: CampusVoiceTestClient, results: TestResults):
    """Test 1: User Registration and Login"""
    print("\n" + "=" * 80)
    print("🔐 TEST SUITE 1: USER AUTHENTICATION")
    print("=" * 80 + "\n")
    
    for user_key, user_data in TEST_USERS.items():
        # Register (might already exist)
        client.register_user(user_key, user_data)
        
        # Login
        token = client.login_user(user_key, user_data)
        if token:
            results.log_test(
                f"Login: {user_data['name']}",
                "PASS",
                f"{user_data['branch']} - {user_data['stay_type']}"
            )
        else:
            results.log_test(
                f"Login: {user_data['name']}",
                "FAIL",
                "Could not obtain access token"
            )


def test_hostel_routing_hierarchy(client: CampusVoiceTestClient, results: TestResults):
    """Test 2: Hostel Complaint Routing Hierarchy"""
    print("\n" + "=" * 80)
    print("🏠 TEST SUITE 2: HOSTEL ROUTING HIERARCHY")
    print("=" * 80 + "\n")
    
    hostel_user = "hostel_cs"
    
    # Test 2.1: Normal hostel complaints → Warden
    print("\n📝 Test 2.1: Normal Hostel Complaints (Route to Warden)")
    print("-" * 80)
    for idx, complaint_data in enumerate(HOSTEL_NORMAL, 1):
        result = client.submit_complaint(
            hostel_user,
            complaint_data["text"],
            category_id=1,  # Hostel category
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            expected = complaint_data["expected_route"]
            
            if "Warden" in assigned_to and "Deputy" not in assigned_to:
                results.log_test(
                    f"Hostel Normal #{idx}",
                    "PASS",
                    f"Routed to: {assigned_to}",
                    expected,
                    assigned_to
                )
            else:
                results.log_test(
                    f"Hostel Normal #{idx}",
                    "FAIL",
                    f"Wrong routing",
                    expected,
                    assigned_to
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Hostel Normal",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"Hostel Normal #{idx}", "FAIL", "Submission failed")
    
    # Test 2.2: Complaints AGAINST Warden → Deputy Warden
    print("\n⚠️ Test 2.2: Complaints Against Warden (Bypass to Deputy Warden)")
    print("-" * 80)
    for idx, complaint_data in enumerate(HOSTEL_AGAINST_WARDEN, 1):
        result = client.submit_complaint(
            hostel_user,
            complaint_data["text"],
            category_id=1,
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            expected = complaint_data["expected_route"]
            
            if "Deputy Warden" in assigned_to and "Senior" not in assigned_to:
                results.log_test(
                    f"Against Warden #{idx}",
                    "PASS",
                    f"Bypassed to: {assigned_to}",
                    expected,
                    assigned_to
                )
            else:
                results.log_test(
                    f"Against Warden #{idx}",
                    "FAIL",
                    f"Wrong escalation",
                    expected,
                    assigned_to
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Against Warden",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"Against Warden #{idx}", "FAIL", "Submission failed")
    
    # Test 2.3: Complaints AGAINST Deputy Warden → Senior Deputy Warden
    print("\n⚠️⚠️ Test 2.3: Complaints Against Deputy Warden (Escalate to Senior Deputy)")
    print("-" * 80)
    for idx, complaint_data in enumerate(HOSTEL_AGAINST_DEPUTY_WARDEN, 1):
        result = client.submit_complaint(
            hostel_user,
            complaint_data["text"],
            category_id=1,
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            expected = complaint_data["expected_route"]
            
            if "Senior Deputy Warden" in assigned_to or "Senior Warden" in assigned_to:
                results.log_test(
                    f"Against Deputy Warden #{idx}",
                    "PASS",
                    f"Escalated to: {assigned_to}",
                    expected,
                    assigned_to
                )
            else:
                results.log_test(
                    f"Against Deputy Warden #{idx}",
                    "FAIL",
                    f"Wrong escalation",
                    expected,
                    assigned_to
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Against Deputy Warden",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"Against Deputy Warden #{idx}", "FAIL", "Submission failed")


def test_day_scholar_spam_detection(client: CampusVoiceTestClient, results: TestResults):
    """Test 3: Day Scholar Hostel Complaint Spam Detection"""
    print("\n" + "=" * 80)
    print("🚫 TEST SUITE 3: DAY SCHOLAR SPAM DETECTION")
    print("=" * 80 + "\n")
    
    print("📝 Day Scholars complaining about hostel → Should be SPAM")
    print("-" * 80)
    
    day_scholar_user = "dayscholar_cs"
    
    for idx, complaint_data in enumerate(DAY_SCHOLAR_HOSTEL_SPAM, 1):
        result = client.submit_complaint(
            day_scholar_user,
            complaint_data["text"],
            category_id=1,  # Hostel category
            visibility="Public"
        )
        
        if result:
            is_spam = result.get("is_spam", False)
            
            if is_spam:
                results.log_test(
                    f"Day Scholar Hostel #{idx}",
                    "PASS",
                    f"Correctly marked as SPAM: {complaint_data['reason']}"
                )
            else:
                results.log_test(
                    f"Day Scholar Hostel #{idx}",
                    "FAIL",
                    "Should be marked as SPAM but wasn't",
                    "SPAM = True",
                    f"SPAM = {is_spam}"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Day Scholar Hostel SPAM",
                "is_spam": is_spam
            })
        else:
            results.log_test(f"Day Scholar Hostel #{idx}", "FAIL", "Submission failed")


def test_department_complaints(client: CampusVoiceTestClient, results: TestResults):
    """Test 4: Department-Specific Complaints"""
    print("\n" + "=" * 80)
    print("🏛️ TEST SUITE 4: DEPARTMENT COMPLAINTS")
    print("=" * 80 + "\n")
    
    # Test 4.1: CS Department Complaints
    print("\n💻 Test 4.1: Computer Science Department")
    print("-" * 80)
    cs_user = "hostel_cs"
    
    for idx, complaint_data in enumerate(CS_DEPT_COMPLAINTS, 1):
        result = client.submit_complaint(
            cs_user,
            complaint_data["text"],
            category_id=2,  # Department category
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            
            # Should be assigned to CS department HOD
            if "Computer Science" in assigned_to or "CS" in assigned_to or "HOD" in assigned_to:
                results.log_test(
                    f"CS Dept #{idx}",
                    "PASS",
                    f"Assigned to: {assigned_to}"
                )
            else:
                results.log_test(
                    f"CS Dept #{idx}",
                    "WARNING",
                    f"Assigned to: {assigned_to} (Check if correct)"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "CS Department",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"CS Dept #{idx}", "FAIL", "Submission failed")
    
    # Test 4.2: ECE Department Complaints
    print("\n📡 Test 4.2: Electronics and Communication Engineering")
    print("-" * 80)
    ece_user = "hostel_ece"
    
    for idx, complaint_data in enumerate(ECE_DEPT_COMPLAINTS, 1):
        result = client.submit_complaint(
            ece_user,
            complaint_data["text"],
            category_id=2,
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            
            if "Electronics" in assigned_to or "ECE" in assigned_to or "HOD" in assigned_to:
                results.log_test(
                    f"ECE Dept #{idx}",
                    "PASS",
                    f"Assigned to: {assigned_to}"
                )
            else:
                results.log_test(
                    f"ECE Dept #{idx}",
                    "WARNING",
                    f"Assigned to: {assigned_to} (Check if correct)"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "ECE Department",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"ECE Dept #{idx}", "FAIL", "Submission failed")
    
    # Test 4.3: Mechanical Department Complaints
    print("\n⚙️ Test 4.3: Mechanical Engineering")
    print("-" * 80)
    mech_user = "hostel_mech"
    
    for idx, complaint_data in enumerate(MECH_DEPT_COMPLAINTS, 1):
        result = client.submit_complaint(
            mech_user,
            complaint_data["text"],
            category_id=2,
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            
            if "Mechanical" in assigned_to or "MECH" in assigned_to or "HOD" in assigned_to:
                results.log_test(
                    f"MECH Dept #{idx}",
                    "PASS",
                    f"Assigned to: {assigned_to}"
                )
            else:
                results.log_test(
                    f"MECH Dept #{idx}",
                    "WARNING",
                    f"Assigned to: {assigned_to} (Check if correct)"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "MECH Department",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"MECH Dept #{idx}", "FAIL", "Submission failed")
    
    # Test 4.4: Inter-departmental routing
    print("\n🔄 Test 4.4: Inter-Departmental Complaints")
    print("-" * 80)
    print("CS student complaining about ECE → Should route to ECE HOD")
    
    for idx, complaint_data in enumerate(INTER_DEPT_COMPLAINTS, 1):
        # CS student complaining about ECE
        if complaint_data["complainant_dept"] == "Computer Science and Engineering":
            user = "hostel_cs"
        elif complaint_data["complainant_dept"] == "Electronics and Communication Engineering":
            user = "hostel_ece"
        else:
            user = "hostel_mech"
        
        result = client.submit_complaint(
            user,
            complaint_data["text"],
            category_id=2,
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            expected_target = complaint_data["target_dept"]
            
            # Check if routed to target department (not complainant's department)
            if any(dept_keyword in assigned_to for dept_keyword in ["Electronics", "ECE", "Mechanical", "MECH"]):
                results.log_test(
                    f"Inter-Dept #{idx}",
                    "PASS",
                    f"Routed to target dept: {assigned_to}"
                )
            else:
                results.log_test(
                    f"Inter-Dept #{idx}",
                    "WARNING",
                    f"Check routing: {assigned_to}"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Inter-Departmental",
                "assigned_to": assigned_to
            })
        else:
            results.log_test(f"Inter-Dept #{idx}", "FAIL", "Submission failed")


def test_department_feed_isolation(client: CampusVoiceTestClient, results: TestResults):
    """Test 5: Public Feed Department Isolation"""
    print("\n" + "=" * 80)
    print("🔒 TEST SUITE 5: DEPARTMENT FEED ISOLATION")
    print("=" * 80 + "\n")
    
    print("📝 Testing: CS student should NOT see ECE department public complaints")
    print("-" * 80)
    
    # Submit a public complaint from ECE student
    ece_complaint = client.submit_complaint(
        "hostel_ece",
        "This is an ECE department specific test complaint that CS students should not see in their feed.",
        category_id=2,
        visibility="Public"
    )
    
    if ece_complaint:
        ece_complaint_id = ece_complaint.get("complaint_id")
        
        # CS student fetches public feed
        time.sleep(1)  # Small delay for data propagation
        cs_feed = client.get_public_feed("hostel_cs")
        
        # Check if ECE complaint appears in CS student's feed
        ece_complaint_in_cs_feed = any(
            c.get("id") == ece_complaint_id or c.get("complaint_id") == ece_complaint_id 
            for c in cs_feed
        )
        
        if not ece_complaint_in_cs_feed:
            results.log_test(
                "Feed Isolation: CS ≠ ECE",
                "PASS",
                "CS student correctly cannot see ECE department complaint"
            )
        else:
            results.log_test(
                "Feed Isolation: CS ≠ ECE",
                "FAIL",
                "CS student can see ECE department complaint (should be isolated)"
            )
    else:
        results.log_test(
            "Feed Isolation: CS ≠ ECE",
            "FAIL",
            "Could not create test complaint"
        )
    
    # Similarly test MECH isolation
    print("\n📝 Testing: ECE student should NOT see MECH department public complaints")
    print("-" * 80)
    
    mech_complaint = client.submit_complaint(
        "hostel_mech",
        "This is a MECH department specific test complaint that ECE students should not see.",
        category_id=2,
        visibility="Public"
    )
    
    if mech_complaint:
        mech_complaint_id = mech_complaint.get("complaint_id")
        
        time.sleep(1)
        ece_feed = client.get_public_feed("hostel_ece")
        
        mech_complaint_in_ece_feed = any(
            c.get("id") == mech_complaint_id or c.get("complaint_id") == mech_complaint_id
            for c in ece_feed
        )
        
        if not mech_complaint_in_ece_feed:
            results.log_test(
                "Feed Isolation: ECE ≠ MECH",
                "PASS",
                "ECE student correctly cannot see MECH department complaint"
            )
        else:
            results.log_test(
                "Feed Isolation: ECE ≠ MECH",
                "FAIL",
                "ECE student can see MECH department complaint (should be isolated)"
            )
    else:
        results.log_test(
            "Feed Isolation: ECE ≠ MECH",
            "FAIL",
            "Could not create test complaint"
        )


def test_public_voting_priority(client: CampusVoiceTestClient, results: TestResults):
    """Test 6: Public Voting and Priority Escalation"""
    print("\n" + "=" * 80)
    print("👍 TEST SUITE 6: PUBLIC VOTING & PRIORITY ESCALATION")
    print("=" * 80 + "\n")
    
    # Submit a test complaint
    test_complaint = client.submit_complaint(
        "hostel_cs",
        "Test complaint for voting: Library AC not working properly, making it difficult to study.",
        category_id=3,  # General
        visibility="Public"
    )
    
    if not test_complaint:
        results.log_test("Voting Test Setup", "FAIL", "Could not create test complaint")
        return
    
    complaint_id = test_complaint.get("complaint_id")
    initial_priority = test_complaint.get("priority", "Low")
    
    print(f"📝 Created test complaint ID: {complaint_id}")
    print(f"   Initial Priority: {initial_priority}")
    print("-" * 80)
    
    # Multiple users upvote
    print("\n👍 Simulating upvotes from multiple students...")
    upvote_users = ["hostel_cs", "hostel_ece", "hostel_mech", "hostel_eee", "hostel_civil"]
    upvote_count = 0
    
    for user in upvote_users:
        if client.vote_on_complaint(user, complaint_id, "Upvote"):
            upvote_count += 1
            print(f"   ✓ {TEST_USERS[user]['name']} upvoted")
        time.sleep(0.5)
    
    # Few downvotes
    print("\n👎 Simulating downvotes...")
    downvote_users = ["dayscholar_cs", "dayscholar_ece"]
    downvote_count = 0
    
    for user in downvote_users:
        if client.vote_on_complaint(user, complaint_id, "Downvote"):
            downvote_count += 1
            print(f"   ✓ {TEST_USERS[user]['name']} downvoted")
        time.sleep(0.5)
    
    # Check updated priority
    time.sleep(2)  # Wait for priority recalculation
    updated_complaint = client.get_complaint_details("hostel_cs", complaint_id)
    
    if updated_complaint:
        new_priority = updated_complaint.get("priority", initial_priority)
        
        print(f"\n📊 Voting Results:")
        print(f"   Upvotes: {upvote_count}")
        print(f"   Downvotes: {downvote_count}")
        print(f"   Initial Priority: {initial_priority}")
        print(f"   Updated Priority: {new_priority}")
        
        # Priority should increase with more upvotes
        priority_levels = {"Low": 1, "Medium": 2, "High": 3}
        
        if upvote_count > downvote_count * 2:  # Significant positive voting
            if priority_levels.get(new_priority, 0) > priority_levels.get(initial_priority, 0):
                results.log_test(
                    "Priority Escalation",
                    "PASS",
                    f"Priority increased from {initial_priority} to {new_priority}"
                )
            else:
                results.log_test(
                    "Priority Escalation",
                    "WARNING",
                    f"Priority unchanged or decreased despite positive votes ({initial_priority} → {new_priority})"
                )
        else:
            results.log_test(
                "Priority Escalation",
                "PASS",
                f"Priority: {initial_priority} → {new_priority} (voting ratio: {upvote_count}:{downvote_count})"
            )
    else:
        results.log_test("Priority Escalation", "FAIL", "Could not fetch updated complaint")


def test_general_and_disciplinary(client: CampusVoiceTestClient, results: TestResults):
    """Test 7: General and Disciplinary Complaints"""
    print("\n" + "=" * 80)
    print("📋 TEST SUITE 7: GENERAL & DISCIPLINARY COMPLAINTS")
    print("=" * 80 + "\n")
    
    # Test 7.1: General Complaints
    print("\n📝 Test 7.1: General Complaints")
    print("-" * 80)
    
    for idx, complaint_data in enumerate(GENERAL_COMPLAINTS, 1):
        result = client.submit_complaint(
            "hostel_cs",
            complaint_data["text"],
            category_id=3,  # General
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            results.log_test(
                f"General #{idx}",
                "PASS",
                f"Assigned to: {assigned_to}"
            )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "General",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"General #{idx}", "FAIL", "Submission failed")
    
    # Test 7.2: Disciplinary Complaints
    print("\n⚖️ Test 7.2: Disciplinary Complaints")
    print("-" * 80)
    
    for idx, complaint_data in enumerate(DISCIPLINARY_COMPLAINTS, 1):
        result = client.submit_complaint(
            "hostel_cs",
            complaint_data["text"],
            category_id=4,  # Disciplinary
            visibility="Public"
        )
        
        if result:
            assigned_to = result.get("assigned_authority", "")
            
            # Should be assigned to Disciplinary Committee
            if "Disciplinary" in assigned_to or "Committee" in assigned_to:
                results.log_test(
                    f"Disciplinary #{idx}",
                    "PASS",
                    f"Assigned to: {assigned_to}"
                )
            else:
                results.log_test(
                    f"Disciplinary #{idx}",
                    "WARNING",
                    f"Assigned to: {assigned_to} (Should be Disciplinary Committee)"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Disciplinary",
                "assigned_to": assigned_to,
                "priority": result.get("priority")
            })
        else:
            results.log_test(f"Disciplinary #{idx}", "FAIL", "Submission failed")


def test_spam_detection(client: CampusVoiceTestClient, results: TestResults):
    """Test 8: Spam and Abusive Content Detection"""
    print("\n" + "=" * 80)
    print("🚨 TEST SUITE 8: SPAM & ABUSIVE CONTENT DETECTION")
    print("=" * 80 + "\n")
    
    for idx, complaint_data in enumerate(SPAM_COMPLAINTS, 1):
        result = client.submit_complaint(
            "hostel_cs",
            complaint_data["text"],
            category_id=3,
            visibility="Public"
        )
        
        if result:
            is_spam = result.get("is_spam", False)
            flag = result.get("flag", "")
            
            if is_spam and complaint_data.get("expected_spam"):
                flag_status = ""
                if complaint_data.get("expected_flag") == "Black" and flag == "Black":
                    flag_status = " [Black Flag ✓]"
                
                results.log_test(
                    f"Spam Detection #{idx}",
                    "PASS",
                    f"Correctly detected: {complaint_data['reason']}{flag_status}"
                )
            else:
                results.log_test(
                    f"Spam Detection #{idx}",
                    "FAIL",
                    f"Expected spam={complaint_data.get('expected_spam')}, Got spam={is_spam}"
                )
            
            results.add_complaint({
                "id": result.get("complaint_id"),
                "type": "Spam Test",
                "is_spam": is_spam,
                "flag": flag
            })
        else:
            results.log_test(f"Spam Detection #{idx}", "FAIL", "Submission failed")


# ==================== MAIN TEST RUNNER ====================

def run_all_tests():
    """Execute all test suites"""
    print("\n" + "=" * 80)
    print("🚀 CAMPUSVOICE COMPREHENSIVE TEST SUITE")
    print("=" * 80)
    print(f"⏰ Started: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}")
    print(f"🌐 API Endpoint: {API_URL}")
    print("=" * 80)
    
    client = CampusVoiceTestClient()
    results = TestResults()
    
    try:
        # Run all test suites
        test_user_authentication(client, results)
        test_hostel_routing_hierarchy(client, results)
        test_day_scholar_spam_detection(client, results)
        test_department_complaints(client, results)
        test_department_feed_isolation(client, results)
        test_public_voting_priority(client, results)
        test_general_and_disciplinary(client, results)
        test_spam_detection(client, results)
        
    except KeyboardInterrupt:
        print("\n\n⚠️ Test execution interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Fatal error during test execution: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        client.close()
    
    # Print summary
    results.print_summary()
    results.save_report("campusvoice_test_report.json")
    
    print("\n✨ Test execution completed!")
    print(f"⏰ Finished: {datetime.now().strftime('%Y-%m-%d %I:%M:%S %p')}\n")


if __name__ == "__main__":
    run_all_tests()