"""
CampusVoice Services Testing Dashboard
Comprehensive manual testing interface for all services

Run with: streamlit run test_services_dashboard.py
"""

import streamlit as st
import asyncio
import sys
from pathlib import Path
from datetime import datetime
import json
from uuid import uuid4, UUID

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Configure Streamlit page
st.set_page_config(
    page_title="CampusVoice Services Dashboard",
    page_icon="🎓",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        padding: 1rem;
        background: linear-gradient(90deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }
    .service-card {
        padding: 1.5rem;
        border-radius: 10px;
        background-color: #f0f2f6;
        margin: 1rem 0;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .success-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d4edda;
        border: 1px solid #c3e6cb;
        color: #155724;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #f8d7da;
        border: 1px solid #f5c6cb;
        color: #721c24;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        border-radius: 5px;
        background-color: #d1ecf1;
        border: 1px solid #bee5eb;
        color: #0c5460;
        margin: 1rem 0;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3rem;
        font-weight: bold;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'test_results' not in st.session_state:
    st.session_state.test_results = {}
if 'current_token' not in st.session_state:
    st.session_state.current_token = None

# Helper function to run async code
def run_async(coro):
    """Run async coroutine and return result"""
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()

# ==================== MAIN HEADER ====================
st.markdown('<h1 class="main-header">🎓 CampusVoice Services Testing Dashboard</h1>', unsafe_allow_html=True)
st.markdown("---")

# ==================== SIDEBAR ====================
with st.sidebar:
    st.header("📋 Test Categories")
    
    test_category = st.selectbox(
        "Select Service to Test",
        [
            "🔐 Authentication",
            "🤖 LLM Service",
            "🚫 Spam Detection",
            "🖼️ Image Verification",
            "👍 Voting System",
            "🔔 Notifications",
            "👮 Authority Service",
            "📢 Authority Updates",
            "📝 Complaint Service",
            "🔍 All Services Overview"
        ]
    )
    
    st.markdown("---")
    st.info("💡 **Tip:** Test each service independently to ensure functionality")
    
    # Connection status
    st.markdown("### 📡 Connection Status")
    
    try:
        from src.services import (
            auth_service,
            llm_service,
            spam_detection_service,
            image_verification_service
        )
        st.success("✅ Services loaded")
    except Exception as e:
        st.error(f"❌ Import error: {e}")

# ==================== TEST SECTION: AUTHENTICATION ====================
if test_category == "🔐 Authentication":
    st.header("🔐 Authentication Service Testing")
    
    tab1, tab2, tab3 = st.tabs(["Password Hashing", "JWT Tokens", "Token Verification"])
    
    with tab1:
        st.subheader("🔒 Password Hashing Test")
        
        col1, col2 = st.columns(2)
        
        with col1:
            password = st.text_input("Enter Password", type="password", value="TestPassword123!")
            
            if st.button("🔨 Hash Password"):
                try:
                    from src.services import auth_service
                    
                    with st.spinner("Hashing password..."):
                        hashed = auth_service.hash_password(password)
                        
                    st.success("✅ Password hashed successfully!")
                    st.code(hashed, language="text")
                    
                    # Verify
                    is_valid = auth_service.verify_password(password, hashed)
                    if is_valid:
                        st.success("✅ Password verification works!")
                    else:
                        st.error("❌ Password verification failed!")
                        
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            st.info("""
            **Password Hashing**
            - Uses bcrypt algorithm
            - Secure one-way hashing
            - Automatic salt generation
            - Verification without storing plain text
            """)
    
    with tab2:
        st.subheader("🎫 JWT Token Generation")
        
        col1, col2 = st.columns(2)
        
        with col1:
            roll_no = st.text_input("Roll Number", value="22CS231")
            role = st.selectbox("Role", ["Student", "Authority"])
            
            col_a, col_b = st.columns(2)
            
            with col_a:
                if st.button("🎟️ Generate Access Token"):
                    try:
                        from src.services import auth_service
                        
                        token = auth_service.create_access_token(roll_no, role)
                        st.session_state.current_token = token
                        
                        st.success("✅ Access token generated!")
                        st.code(token, language="text")
                        st.info(f"Token length: {len(token)} characters")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
            
            with col_b:
                if st.button("🔄 Generate Refresh Token"):
                    try:
                        from src.services import auth_service
                        
                        token = auth_service.create_refresh_token(roll_no, role)
                        
                        st.success("✅ Refresh token generated!")
                        st.code(token, language="text")
                        
                    except Exception as e:
                        st.error(f"❌ Error: {e}")
        
        with col2:
            st.info("""
            **JWT Tokens**
            - Access Token: Short-lived (7 days)
            - Refresh Token: Long-lived (30 days)
            - Contains user identity and role
            - Cryptographically signed
            """)
    
    with tab3:
        st.subheader("🔍 Token Verification")
        
        token_to_verify = st.text_area("Paste JWT Token", value=st.session_state.current_token or "")
        
        if st.button("✅ Verify Token"):
            try:
                from src.services import auth_service
                
                with st.spinner("Verifying token..."):
                    # Try different method names
                    if hasattr(auth_service, 'verify_access_token'):
                        payload = auth_service.verify_access_token(token_to_verify)
                    elif hasattr(auth_service, 'decode_token'):
                        payload = auth_service.decode_token(token_to_verify)
                    else:
                        st.error("❌ No verification method found")
                        payload = None
                
                if payload:
                    st.success("✅ Token is valid!")
                    st.json(payload)
                    
                    # Extract info
                    user_id = payload.get('sub') or payload.get('roll_no')
                    role = payload.get('role')
                    exp = payload.get('exp')
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("User ID", user_id)
                    with col2:
                        st.metric("Role", role)
                    with col3:
                        exp_time = datetime.fromtimestamp(exp) if exp else "N/A"
                        st.metric("Expires", str(exp_time)[:19])
                
            except Exception as e:
                st.error(f"❌ Token verification failed: {e}")

# ==================== TEST SECTION: LLM SERVICE ====================
elif test_category == "🤖 LLM Service":
    st.header("🤖 LLM Service Testing (Groq API)")
    
    tab1, tab2, tab3, tab4 = st.tabs(["API Connection", "Categorization", "Rephrasing", "Spam Detection"])
    
    with tab1:
        st.subheader("📡 Groq API Connection Test")
        
        if st.button("🔌 Test Connection"):
            try:
                from src.services import llm_service
                
                with st.spinner("Connecting to Groq API..."):
                    result = run_async(llm_service.test_connection())
                
                if result['status'] == 'success':
                    st.success("✅ Groq API connected successfully!")
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Model", result['model'])
                    with col2:
                        st.metric("Response Time", f"{result['response_time_ms']}ms")
                    with col3:
                        st.metric("Status", "✅ Online")
                    
                    st.json(result)
                else:
                    st.error(f"❌ Connection failed: {result['message']}")
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("📂 Complaint Categorization")
        
        complaint_text = st.text_area(
            "Enter Complaint Text",
            value="The AC in my hostel room 301 is not working. It's very hot and uncomfortable.",
            height=150
        )
        
        col1, col2 = st.columns(2)
        
        with col1:
            gender = st.selectbox("Gender", ["Male", "Female", "Other"])
            stay_type = st.selectbox("Stay Type", ["Hosteller", "Day Scholar"])
        
        with col2:
            department = st.selectbox("Department", [
                "Computer Science", "Electronics", "Mechanical",
                "Civil", "Electrical", "Information Technology"
            ])
            year = st.selectbox("Year", ["1st Year", "2nd Year", "3rd Year", "4th Year"])
        
        if st.button("🎯 Categorize Complaint"):
            try:
                from src.services import llm_service
                
                context = {
                    "gender": gender,
                    "stay_type": stay_type,
                    "department": department,
                    "year": year
                }
                
                with st.spinner("Categorizing complaint..."):
                    result = run_async(llm_service.categorize_complaint(complaint_text, context))
                
                st.success("✅ Categorization complete!")
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Category", result['category'])
                with col2:
                    st.metric("Priority", result['priority'])
                with col3:
                    st.metric("Tokens Used", result.get('tokens_used', 'N/A'))
                with col4:
                    st.metric("Processing Time", f"{result.get('processing_time_ms', 'N/A')}ms")
                
                st.markdown("### 💡 Reasoning")
                st.info(result.get('reasoning', 'No reasoning provided'))
                
                st.markdown("### 📊 Full Result")
                st.json(result)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with tab3:
        st.subheader("✍️ Complaint Rephrasing")
        
        informal_text = st.text_area(
            "Enter Informal Complaint",
            value="bro the canteen food is really bad man its so expensive and tastes horrible!!!",
            height=150
        )
        
        if st.button("✨ Rephrase Complaint"):
            try:
                from src.services import llm_service
                
                with st.spinner("Rephrasing complaint..."):
                    result = run_async(llm_service.rephrase_complaint(informal_text))
                
                st.success("✅ Complaint rephrased successfully!")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.markdown("### 📝 Original")
                    st.text_area("", informal_text, height=200, disabled=True)
                
                with col2:
                    st.markdown("### ✨ Rephrased")
                    st.text_area("", result, height=200, disabled=True)
                
                # Stats
                st.markdown("### 📊 Statistics")
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.metric("Original Length", len(informal_text))
                with col2:
                    st.metric("Rephrased Length", len(result))
                with col3:
                    change_pct = ((len(result) - len(informal_text)) / len(informal_text) * 100)
                    st.metric("Length Change", f"{change_pct:+.1f}%")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
    
    with tab4:
        st.subheader("🚫 LLM-based Spam Detection")
        
        test_text = st.text_area(
            "Enter Text to Check",
            value="asdf qwerty test test spam",
            height=150
        )
        
        if st.button("🔍 Detect Spam"):
            try:
                from src.services import llm_service
                
                with st.spinner("Analyzing text..."):
                    result = run_async(llm_service.detect_spam(test_text))
                
                if result['is_spam']:
                    st.error("🚫 Text detected as SPAM!")
                else:
                    st.success("✅ Text is NOT spam")
                
                col1, col2 = st.columns(2)
                with col1:
                    st.metric("Is Spam?", "Yes" if result['is_spam'] else "No")
                with col2:
                    st.metric("Confidence", f"{result['confidence']:.2f}")
                
                st.markdown("### 💭 Reason")
                st.info(result.get('reason', 'No reason provided'))
                
                st.json(result)
                
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ==================== TEST SECTION: SPAM DETECTION ====================
elif test_category == "🚫 Spam Detection":
    st.header("🚫 Spam Detection Service Testing")
    
    tab1, tab2 = st.tabs(["Keyword Detection", "Blacklist Management"])
    
    with tab1:
        st.subheader("🔍 Spam Keyword Detection")
        
        text_to_check = st.text_area(
            "Enter Text",
            value="This is spam advertising. Click here to buy cheap products!",
            height=150
        )
        
        if st.button("🔍 Check for Spam"):
            try:
                from src.services import spam_detection_service
                
                with st.spinner("Checking for spam..."):
                    # Try different method names
                    if hasattr(spam_detection_service, 'detect_spam'):
                        result = run_async(spam_detection_service.detect_spam(text_to_check))
                    elif hasattr(spam_detection_service, 'check_spam'):
                        result = run_async(spam_detection_service.check_spam(text_to_check))
                    elif hasattr(spam_detection_service, 'is_spam'):
                        result = run_async(spam_detection_service.is_spam(text_to_check))
                    else:
                        st.error("No spam detection method found")
                        result = None
                
                if result:
                    is_spam = result.get('is_spam', False) if isinstance(result, dict) else result
                    
                    if is_spam:
                        st.error("🚫 SPAM DETECTED!")
                    else:
                        st.success("✅ No spam detected")
                    
                    if isinstance(result, dict):
                        st.json(result)
                    else:
                        st.info(f"Result: {result}")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        # Show spam keywords
        st.markdown("### 📋 Spam Keywords")
        try:
            from src.config.constants import SPAM_KEYWORDS
            st.write(", ".join(SPAM_KEYWORDS))
        except:
            st.info("Spam keywords not available")
    
    with tab2:
        st.subheader("🚷 Blacklist Management")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("#### ➕ Add to Blacklist")
            roll_no_add = st.text_input("Roll Number (Add)", value="TEST999")
            reason = st.text_input("Reason", value="Testing blacklist")
            
            if st.button("🚫 Add to Blacklist"):
                try:
                    from src.services import spam_detection_service
                    
                    run_async(spam_detection_service.add_to_blacklist(roll_no_add, reason))
                    st.success(f"✅ {roll_no_add} added to blacklist!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            st.markdown("#### ➖ Remove from Blacklist")
            roll_no_remove = st.text_input("Roll Number (Remove)", value="TEST999")
            
            if st.button("✅ Remove from Blacklist"):
                try:
                    from src.services import spam_detection_service
                    
                    run_async(spam_detection_service.remove_from_blacklist(roll_no_remove))
                    st.success(f"✅ {roll_no_remove} removed from blacklist!")
                    
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        st.markdown("---")
        st.markdown("#### 🔍 Check Blacklist Status")
        
        roll_no_check = st.text_input("Roll Number (Check)", value="TEST999")
        
        if st.button("🔍 Check Status"):
            try:
                from src.services import spam_detection_service
                
                is_blacklisted = run_async(spam_detection_service.is_blacklisted(roll_no_check))
                
                if is_blacklisted:
                    st.error(f"🚫 {roll_no_check} is BLACKLISTED")
                else:
                    st.success(f"✅ {roll_no_check} is NOT blacklisted")
                    
            except Exception as e:
                st.error(f"❌ Error: {e}")

# ==================== TEST SECTION: IMAGE VERIFICATION ====================
elif test_category == "🖼️ Image Verification":
    st.header("🖼️ Image Verification Service Testing")
    
    st.warning("⚠️ **Note:** Image verification requires real image URLs and Groq Vision API access")
    
    tab1, tab2 = st.tabs(["Single Image Verification", "Batch Analysis"])
    
    with tab1:
        st.subheader("🔍 Verify Single Image")
        
        image_url = st.text_input(
            "Image URL",
            value="https://example.com/image.jpg",
            help="Enter a valid image URL (HTTPS only)"
        )
        
        complaint_text = st.text_area(
            "Complaint Text",
            value="The hostel room ceiling has water leakage and damage",
            height=100
        )
        
        complaint_id = st.text_input("Complaint ID (UUID)", value=str(uuid4()))
        
        if st.button("🔍 Verify Image"):
            try:
                from src.services import image_verification_service
                
                with st.spinner("Verifying image..."):
                    # Mock database session
                    class MockDB:
                        pass
                    
                    try:
                        result = run_async(image_verification_service.verify_image(
                            db=MockDB(),
                            complaint_id=UUID(complaint_id),
                            image_url=image_url,
                            complaint_text=complaint_text
                        ))
                        
                        st.success("✅ Image verified!")
                        
                        col1, col2 = st.columns(2)
                        with col1:
                            st.metric("Relevant?", "Yes" if result.get('is_relevant') else "No")
                        with col2:
                            st.metric("Confidence", f"{result.get('confidence', 0):.2f}")
                        
                        st.markdown("### 📝 Analysis")
                        st.info(result.get('reason', 'No reason provided'))
                        
                        st.json(result)
                        
                    except Exception as verify_error:
                        st.error(f"⚠️ Verification error: {verify_error}")
                        st.info("This is expected with placeholder URLs. Use real image URLs for actual testing.")
                
            except Exception as e:
                st.error(f"❌ Error: {e}")
        
        # Display image if URL provided
        if image_url and image_url.startswith("http"):
            try:
                st.image(image_url, caption="Image Preview", use_container_width=True)
            except:
                st.warning("Unable to display image preview")
    
    with tab2:
        st.subheader("📊 Batch Image Analysis")
        
        st.info("💡 Upload multiple image URLs (one per line)")
        
        urls_text = st.text_area(
            "Image URLs",
            value="https://example.com/image1.jpg\nhttps://example.com/image2.jpg",
            height=200
        )
        
        batch_complaint = st.text_input("Complaint Text", value="Multiple damage issues")
        
        if st.button("🔍 Analyze Batch"):
            urls = [url.strip() for url in urls_text.split('\n') if url.strip()]
            
            if not urls:
                st.error("No URLs provided")
            else:
                st.info(f"Processing {len(urls)} images...")
                
                for i, url in enumerate(urls, 1):
                    st.markdown(f"#### Image {i}: {url[:50]}...")
                    st.info("Batch processing would verify each image here")

# ==================== TEST SECTION: VOTING SYSTEM ====================
elif test_category == "👍 Voting System":
    st.header("👍 Voting System Testing")
    
    st.info("💡 Vote system requires database. Testing priority calculation logic.")
    
    tab1, tab2 = st.tabs(["Priority Calculation", "Vote Scenarios"])
    
    with tab1:
        st.subheader("📊 Priority Score Calculator")
        
        col1, col2 = st.columns(2)
        
        with col1:
            base_priority = st.selectbox("Base Priority", ["Low", "Medium", "High", "Critical"])
            upvotes = st.number_input("Upvotes", min_value=0, max_value=1000, value=10)
            downvotes = st.number_input("Downvotes", min_value=0, max_value=1000, value=2)
        
        with col2:
            from src.config.constants import PRIORITY_SCORES, VOTE_IMPACT_MULTIPLIER
            
            base_score = PRIORITY_SCORES[base_priority]
            vote_score = upvotes - downvotes
            vote_impact = vote_score * VOTE_IMPACT_MULTIPLIER
            final_score = max(base_score + vote_impact, 0)
            
            st.metric("Base Score", base_score)
            st.metric("Vote Impact", f"{vote_impact:+.1f}")
            st.metric("Final Score", final_score)
            
            # Calculate priority level
            if final_score >= 200:
                final_priority = "Critical"
            elif final_score >= 100:
                final_priority = "High"
            elif final_score >= 50:
                final_priority = "Medium"
            else:
                final_priority = "Low"
            
            st.metric("Final Priority", final_priority)
    
    with tab2:
        st.subheader("🎬 Vote Scenarios")
        
        scenarios = [
            {
                "name": "Low Priority, Few Votes",
                "base": "Low",
                "upvotes": 5,
                "downvotes": 1
            },
            {
                "name": "Medium Priority, Popular",
                "base": "Medium",
                "upvotes": 50,
                "downvotes": 10
            },
            {
                "name": "High Priority, Controversial",
                "base": "High",
                "upvotes": 30,
                "downvotes": 25
            },
            {
                "name": "Critical Priority, Overwhelming Support",
                "base": "Critical",
                "upvotes": 100,
                "downvotes": 5
            }
        ]
        
        for scenario in scenarios:
            with st.expander(f"📌 {scenario['name']}"):
                from src.config.constants import PRIORITY_SCORES, VOTE_IMPACT_MULTIPLIER
                
                base_score = PRIORITY_SCORES[scenario['base']]
                vote_score = scenario['upvotes'] - scenario['downvotes']
                vote_impact = vote_score * VOTE_IMPACT_MULTIPLIER
                final_score = max(base_score + vote_impact, 0)
                
                if final_score >= 200:
                    final_priority = "Critical"
                elif final_score >= 100:
                    final_priority = "High"
                elif final_score >= 50:
                    final_priority = "Medium"
                else:
                    final_priority = "Low"
                
                col1, col2, col3, col4 = st.columns(4)
                with col1:
                    st.metric("Base", scenario['base'])
                with col2:
                    st.metric("Upvotes", scenario['upvotes'])
                with col3:
                    st.metric("Downvotes", scenario['downvotes'])
                with col4:
                    st.metric("Final Priority", final_priority)
                
                st.info(f"Score: {base_score} + ({vote_score} × {VOTE_IMPACT_MULTIPLIER}) = {final_score}")

# ==================== TEST SECTION: NOTIFICATIONS ====================
elif test_category == "🔔 Notifications":
    st.header("🔔 Notification Service Testing")
    
    st.info("💡 Notification system requires database. Testing templates and structure.")
    
    tab1, tab2 = st.tabs(["Notification Templates", "Create Sample"])
    
    with tab1:
        st.subheader("📋 Available Notification Templates")
        
        try:
            from src.services import notification_service
            
            if hasattr(notification_service, 'NOTIFICATION_TEMPLATES'):
                templates = notification_service.NOTIFICATION_TEMPLATES
                
                for key, template in templates.items():
                    with st.expander(f"📨 {key}"):
                        st.code(template, language="text")
                
                st.success(f"✅ {len(templates)} templates available")
            else:
                st.warning("Templates not found in service")
                
        except Exception as e:
            st.error(f"❌ Error: {e}")
    
    with tab2:
        st.subheader("✍️ Create Sample Notification")
        
        recipient_type = st.selectbox("Recipient Type", ["Student", "Authority"])
        recipient_id = st.text_input("Recipient ID", value="22CS231")
        
        notification_type = st.selectbox("Notification Type", [
            "status_update",
            "complaint_assigned",
            "escalation",
            "spam_alert",
            "comment_added",
            "vote_milestone",
            "complaint_resolved"
        ])
        
        message = st.text_area("Message", value="Your complaint status has been updated", height=100)
        
        st.markdown("### 📝 Sample Notification Preview")
        
        sample_notification = {
            "recipient_type": recipient_type,
            "recipient_id": recipient_id,
            "notification_type": notification_type,
            "message": message,
            "is_read": False,
            "created_at": datetime.now().isoformat()
        }
        
        st.json(sample_notification)
        
        st.info("💡 Actual notification creation requires database connection")

# ==================== TEST SECTION: AUTHORITY SERVICE ====================
elif test_category == "👮 Authority Service":
    st.header("👮 Authority Service Testing")
    
    tab1, tab2 = st.tabs(["Complaint Routing", "Escalation"])
    
    with tab1:
        st.subheader("🎯 Complaint Routing Logic")
        
        category = st.selectbox("Complaint Category", [
            "Hostel",
            "General",
            "Department",
            "Disciplinary Committee"
        ])
        
        from src.config.constants import DEFAULT_CATEGORY_ROUTING, AUTHORITY_LEVELS
        
        routed_to = DEFAULT_CATEGORY_ROUTING.get(category, "Unknown")
        authority_level = AUTHORITY_LEVELS.get(routed_to, 0)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Routes To", routed_to)
        with col2:
            st.metric("Authority Level", authority_level)
        
        st.markdown("### 📋 Routing Rules")
        st.json(DEFAULT_CATEGORY_ROUTING)
    
    with tab2:
        st.subheader("⬆️ Escalation Path")
        
        current_authority = st.selectbox("Current Authority", [
            "Warden",
            "Deputy Warden",
            "Senior Deputy Warden",
            "HOD",
            "Admin Officer",
            "Disciplinary Committee",
            "Admin"
        ])
        
        from src.config.constants import ESCALATION_RULES, AUTHORITY_LEVELS
        
        escalates_to = ESCALATION_RULES.get(current_authority, "No escalation")
        
        current_level = AUTHORITY_LEVELS.get(current_authority, 0)
        escalated_level = AUTHORITY_LEVELS.get(escalates_to, 0)
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Current", current_authority)
            st.caption(f"Level: {current_level}")
        with col2:
            st.markdown("### ➡️")
        with col3:
            st.metric("Escalates To", escalates_to)
            st.caption(f"Level: {escalated_level}")
        
        st.markdown("### 🔗 Complete Escalation Chain")
        
        chain = [current_authority]
        next_auth = escalates_to
        
        while next_auth and next_auth != current_authority and next_auth not in chain:
            chain.append(next_auth)
            next_auth = ESCALATION_RULES.get(next_auth)
        
        st.write(" ➡️ ".join(chain))

# ==================== TEST SECTION: AUTHORITY UPDATES ====================
elif test_category == "📢 Authority Updates":
    st.header("📢 Authority Updates Testing")
    
    st.info("💡 Authority updates require database. Testing structure and preview.")
    
    tab1, tab2 = st.tabs(["Create Update", "Update Categories"])
    
    with tab1:
        st.subheader("✍️ Create Sample Update")
        
        update_type = st.selectbox("Update Type", [
            "Announcement",
            "Policy Change",
            "Event",
            "Maintenance",
            "Emergency",
            "General"
        ])
        
        priority = st.selectbox("Priority", ["Low", "Medium", "High", "Urgent"])
        
        visibility = st.selectbox("Visibility", [
            "All Students",
            "Department",
            "Year",
            "Hostel",
            "Day Scholar"
        ])
        
        title = st.text_input("Title", value=f"Important {update_type}")
        content = st.text_area("Content", value=f"This is a sample {update_type.lower()} announcement.", height=150)
        
        if visibility in ["Department", "Year"]:
            target = st.text_input("Target (Department/Year)", value="Computer Science")
        else:
            target = None
        
        st.markdown("### 📝 Update Preview")
        
        sample_update = {
            "update_type": update_type,
            "priority": priority,
            "visibility": visibility,
            "target": target,
            "title": title,
            "content": content,
            "created_at": datetime.now().isoformat()
        }
        
        st.json(sample_update)
        
        # Preview card
        st.markdown("### 💳 Display Preview")
        
        priority_color = {
            "Low": "#28a745",
            "Medium": "#ffc107",
            "High": "#fd7e14",
            "Urgent": "#dc3545"
        }
        
        st.markdown(f"""
        <div style="padding: 1.5rem; border-left: 5px solid {priority_color.get(priority, '#6c757d')}; background-color: #f8f9fa; border-radius: 5px;">
            <h3 style="margin: 0 0 0.5rem 0;">{title}</h3>
            <p style="color: #6c757d; font-size: 0.9rem; margin: 0 0 1rem 0;">
                <strong>{update_type}</strong> • {priority} Priority • {visibility}
            </p>
            <p style="margin: 0;">{content}</p>
        </div>
        """, unsafe_allow_html=True)
    
    with tab2:
        st.subheader("📂 Update Categories")
        
        from src.config.constants import UpdateCategory, UpdatePriority, UpdateVisibility
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("#### Categories")
            for cat in UpdateCategory:
                st.write(f"• {cat.value}")
        
        with col2:
            st.markdown("#### Priorities")
            for pri in UpdatePriority:
                st.write(f"• {pri.value}")
        
        with col3:
            st.markdown("#### Visibility")
            for vis in UpdateVisibility:
                st.write(f"• {vis.value}")

# ==================== TEST SECTION: COMPLAINT SERVICE ====================
elif test_category == "📝 Complaint Service":
    st.header("📝 Complaint Service Testing")
    
    st.info("💡 Complaint operations require database. Testing structure and validation.")
    
    tab1, tab2 = st.tabs(["Create Complaint", "Status Transitions"])
    
    with tab1:
        st.subheader("✍️ Create Sample Complaint")
        
        col1, col2 = st.columns(2)
        
        with col1:
            title = st.text_input("Complaint Title", value="AC not working")
            description = st.text_area("Description", value="The AC in my room is not working properly.", height=150)
            
            category = st.selectbox("Category", ["Hostel", "General", "Department", "Disciplinary Committee"])
            priority = st.selectbox("Priority", ["Low", "Medium", "High", "Critical"])
        
        with col2:
            visibility = st.selectbox("Visibility", ["Private", "Department", "Public"])
            location = st.text_input("Location", value="Hostel Block A, Room 301")
            
            anonymous = st.checkbox("Anonymous", value=False)
        
        st.markdown("### 📝 Complaint Preview")
        
        sample_complaint = {
            "title": title,
            "description": description,
            "category": category,
            "priority": priority,
            "visibility": visibility,
            "location": location,
            "is_anonymous": anonymous,
            "status": "Raised",
            "upvotes": 0,
            "downvotes": 0,
            "created_at": datetime.now().isoformat()
        }
        
        st.json(sample_complaint)
        
        # Validation
        st.markdown("### ✅ Validation")
        
        from src.config.constants import MIN_COMPLAINT_LENGTH, MAX_COMPLAINT_LENGTH
        
        desc_length = len(description)
        is_valid = MIN_COMPLAINT_LENGTH <= desc_length <= MAX_COMPLAINT_LENGTH
        
        if is_valid:
            st.success(f"✅ Description length valid ({desc_length} characters)")
        else:
            st.error(f"❌ Description must be between {MIN_COMPLAINT_LENGTH} and {MAX_COMPLAINT_LENGTH} characters")
    
    with tab2:
        st.subheader("🔄 Status Transitions")
        
        from src.config.constants import VALID_STATUS_TRANSITIONS
        
        current_status = st.selectbox("Current Status", [
            "Raised",
            "In Progress",
            "Resolved",
            "Closed",
            "Spam"
        ])
        
        valid_transitions = VALID_STATUS_TRANSITIONS.get(current_status, [])
        
        st.markdown(f"### ➡️ Valid Transitions from '{current_status}'")
        
        if valid_transitions:
            for transition in valid_transitions:
                st.success(f"✅ {current_status} → {transition}")
        else:
            st.warning(f"⚠️ No valid transitions from '{current_status}'")
        
        st.markdown("### 📋 All Transition Rules")
        
        for status, transitions in VALID_STATUS_TRANSITIONS.items():
            with st.expander(f"From: {status}"):
                if transitions:
                    st.write(", ".join(transitions))
                else:
                    st.write("Terminal state (no transitions)")

# ==================== TEST SECTION: ALL SERVICES OVERVIEW ====================
elif test_category == "🔍 All Services Overview":
    st.header("🔍 All Services Overview")
    
    services_status = []
    
    # Check each service
    try:
        from src.services import auth_service
        services_status.append(("🔐 Auth Service", "✅ Loaded", "green"))
    except:
        services_status.append(("🔐 Auth Service", "❌ Failed", "red"))
    
    try:
        from src.services import llm_service
        # Test connection
        result = run_async(llm_service.test_connection())
        if result['status'] == 'success':
            services_status.append(("🤖 LLM Service", f"✅ Connected ({result['model']})", "green"))
        else:
            services_status.append(("🤖 LLM Service", "⚠️ Loaded (API issue)", "orange"))
    except:
        services_status.append(("🤖 LLM Service", "❌ Failed", "red"))
    
    try:
        from src.services import spam_detection_service
        services_status.append(("🚫 Spam Detection", "✅ Loaded", "green"))
    except:
        services_status.append(("🚫 Spam Detection", "❌ Failed", "red"))
    
    try:
        from src.services import image_verification_service
        services_status.append(("🖼️ Image Verification", "✅ Loaded", "green"))
    except:
        services_status.append(("🖼️ Image Verification", "❌ Failed", "red"))
    
    try:
        from src.services import VoteService
        services_status.append(("👍 Vote Service", "✅ Loaded", "green"))
    except:
        services_status.append(("👍 Vote Service", "❌ Failed", "red"))
    
    try:
        from src.services import notification_service
        services_status.append(("🔔 Notification Service", "✅ Loaded", "green"))
    except:
        services_status.append(("🔔 Notification Service", "❌ Failed", "red"))
    
    try:
        from src.services import authority_service
        services_status.append(("👮 Authority Service", "✅ Loaded", "green"))
    except:
        services_status.append(("👮 Authority Service", "❌ Failed", "red"))
    
    try:
        from src.services import AuthorityUpdateService
        services_status.append(("📢 Authority Updates", "✅ Loaded", "green"))
    except:
        services_status.append(("📢 Authority Updates", "❌ Failed", "red"))
    
    try:
        from src.services import ComplaintService
        services_status.append(("📝 Complaint Service", "✅ Loaded", "green"))
    except:
        services_status.append(("📝 Complaint Service", "❌ Failed", "red"))
    
    # Display status
    st.markdown("### 📊 Service Status")
    
    for name, status, color in services_status:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(name)
        with col2:
            if color == "green":
                st.success(status)
            elif color == "orange":
                st.warning(status)
            else:
                st.error(status)
    
    # Summary metrics
    loaded = sum(1 for _, _, color in services_status if color == "green")
    total = len(services_status)
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Services", total)
    with col2:
        st.metric("Loaded", loaded)
    with col3:
        success_rate = (loaded / total * 100) if total > 0 else 0
        st.metric("Success Rate", f"{success_rate:.1f}%")
    
    if success_rate == 100:
        st.success("🎉 All services loaded successfully!")
    elif success_rate >= 80:
        st.warning("⚠️ Most services loaded")
    else:
        st.error("❌ Several services failed to load")

# ==================== FOOTER ====================
st.markdown("---")
st.markdown("""
<div style="text-align: center; color: #6c757d; padding: 2rem;">
    <p><strong>CampusVoice Services Testing Dashboard</strong></p>
    <p>Version 1.0 • Built with Streamlit</p>
    <p>Use this dashboard to manually test all CampusVoice services</p>
</div>
""", unsafe_allow_html=True)
