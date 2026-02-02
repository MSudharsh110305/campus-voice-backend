"""
Groq Vision API Test Script - UPDATED
Test image analysis with Groq's latest vision models
Run: streamlit run test_groq_vision.py
"""

import streamlit as st
import base64
from groq import Groq
import os
from PIL import Image
import io

# ==================== CONFIGURATION ====================

st.set_page_config(
    page_title="🖼️ Groq Vision API Test",
    page_icon="🔍",
    layout="wide"
)

# ==================== FUNCTIONS ====================

def encode_image_to_base64(image_file) -> tuple[str, str]:
    """
    Convert uploaded image to base64
    Returns: (base64_string, mime_type)
    """
    # Read image bytes
    image_bytes = image_file.read()
    
    # Encode to base64
    base64_image = base64.b64encode(image_bytes).decode('utf-8')
    
    # Determine MIME type
    mime_type_map = {
        'jpg': 'image/jpeg',
        'jpeg': 'image/jpeg',
        'png': 'image/png',
        'gif': 'image/gif',
        'webp': 'image/webp'
    }
    
    file_extension = image_file.name.split('.')[-1].lower()
    mime_type = mime_type_map.get(file_extension, 'image/jpeg')
    
    return base64_image, mime_type


def analyze_image_with_groq(base64_image: str, mime_type: str, api_key: str, prompt: str, model: str) -> str:
    """
    Analyze image using Groq Vision API
    """
    try:
        client = Groq(api_key=api_key)
        
        # Call Groq Vision API
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": [
                        {
                            "type": "text",
                            "text": prompt
                        },
                        {
                            "type": "image_url",
                            "image_url": {
                                "url": f"data:{mime_type};base64,{base64_image}"
                            }
                        }
                    ]
                }
            ],
            model=model,  # ✅ Use selected model
            temperature=0.2,
            max_tokens=1000
        )
        
        return chat_completion.choices[0].message.content
    
    except Exception as e:
        return f"❌ Error: {str(e)}"


# ==================== STREAMLIT UI ====================

st.title("🖼️ Groq Vision API Test")
st.markdown("Test Groq's vision API by uploading an image and getting AI analysis")

st.divider()

# ==================== SIDEBAR ====================

with st.sidebar:
    st.header("⚙️ Configuration")
    
    # API Key input
    api_key = st.text_input(
        "Groq API Key:",
        type="password",
        value=os.getenv("GROQ_API_KEY", ""),
        help="Get your API key from https://console.groq.com"
    )
    
    st.divider()
    
    # Model selection
    st.subheader("🤖 Model Selection")
    
    vision_models = {
        "Llama 4 Scout (Recommended)": "meta-llama/llama-4-scout-17b-16e-instruct",
        "Llama 4 Maverick": "meta-llama/llama-4-maverick-17b-128e-instruct",
    }
    
    selected_model_name = st.selectbox(
        "Select Vision Model:",
        list(vision_models.keys()),
        help="Llama 4 Scout is recommended for most vision tasks"
    )
    
    selected_model = vision_models[selected_model_name]
    
    st.info(f"**Using:** `{selected_model}`")
    
    st.divider()
    
    # Prompt customization
    st.subheader("📝 Analysis Prompt")
    
    prompt_type = st.selectbox(
        "Select Prompt Type:",
        [
            "General Description",
            "Detailed Analysis",
            "Object Detection",
            "Complaint Verification",
            "Spam Detection",
            "Custom Prompt"
        ]
    )
    
    # Predefined prompts
    prompts = {
        "General Description": "What is in this image? Describe it in detail.",
        "Detailed Analysis": "Analyze this image and provide:\n1. What objects/subjects are visible\n2. The setting/location\n3. Any text visible\n4. Overall quality and clarity\n5. Any issues or problems visible",
        "Object Detection": "List all objects you can identify in this image. Be specific and detailed.",
        "Complaint Verification": """Analyze this image for a campus complaint verification system.

Please evaluate:
1. What infrastructure or facilities are visible?
2. Are there any visible problems, damage, or malfunctions?
3. What specific issues can you identify?
4. How would you rate the severity (Low/Medium/High)?
5. Is this image relevant to a campus complaint?

Provide a detailed analysis.""",
        "Spam Detection": """Check if this image is appropriate for a complaint system.

Evaluate:
1. Is there any profanity or inappropriate content?
2. Is this a genuine photo or a meme/screenshot/unrelated image?
3. Does it appear to be spam or fake?
4. Should this be flagged?

Provide reasoning for your assessment."""
    }
    
    if prompt_type == "Custom Prompt":
        custom_prompt = st.text_area(
            "Enter your prompt:",
            "Describe what you see in this image.",
            height=100
        )
        selected_prompt = custom_prompt
    else:
        selected_prompt = prompts[prompt_type]
        st.text_area("Prompt Preview:", selected_prompt, height=200, disabled=True)
    
    st.divider()
    
    # Model info
    st.success("""
    **✅ Current Models (2026)**
    
    **Llama 4 Scout** (Recommended)
    - Best for general vision tasks
    - Multimodal understanding
    - High accuracy
    
    **Llama 4 Maverick**
    - Advanced reasoning
    - Complex scene analysis
    """)
    
    st.warning("""
    **⚠️ Deprecated Models**
    
    - llama-3.2-90b-vision-preview ❌
    - llama-3.2-11b-vision-preview ❌
    - llava-v1.5-7b-4096-preview ❌
    
    Use Llama 4 Scout instead!
    """)

# ==================== MAIN CONTENT ====================

col1, col2 = st.columns(2)

with col1:
    st.header("📤 Upload Image")
    
    uploaded_file = st.file_uploader(
        "Choose an image file:",
        type=['jpg', 'jpeg', 'png', 'gif', 'webp'],
        help="Supported formats: JPG, JPEG, PNG, GIF, WebP"
    )
    
    if uploaded_file:
        # Display uploaded image
        image = Image.open(uploaded_file)
        st.image(image, caption="Uploaded Image", use_container_width=True)
        
        # Show image info
        st.caption(f"**Filename:** {uploaded_file.name}")
        st.caption(f"**Size:** {uploaded_file.size / 1024:.2f} KB")
        st.caption(f"**Dimensions:** {image.size[0]} x {image.size[1]}")

with col2:
    st.header("🔍 AI Analysis")
    
    if not api_key:
        st.warning("⚠️ Please enter your Groq API key in the sidebar")
    elif not uploaded_file:
        st.info("👆 Upload an image to start analysis")
    else:
        # Analyze button
        if st.button("🚀 Analyze Image", type="primary", use_container_width=True):
            with st.spinner(f"🔄 Analyzing with {selected_model_name}..."):
                # Reset file pointer
                uploaded_file.seek(0)
                
                # Encode image
                base64_image, mime_type = encode_image_to_base64(uploaded_file)
                
                # Analyze with Groq
                result = analyze_image_with_groq(
                    base64_image=base64_image,
                    mime_type=mime_type,
                    api_key=api_key,
                    prompt=selected_prompt,
                    model=selected_model
                )
                
                # Display result
                if result.startswith("❌"):
                    st.error(result)
                else:
                    st.success("✅ Analysis Complete!")
                    
                    # Display result in a nice box
                    st.markdown("### 📊 Analysis Result")
                    st.markdown(result)
                    
                    # Save to session state
                    if 'analysis_history' not in st.session_state:
                        st.session_state.analysis_history = []
                    
                    st.session_state.analysis_history.append({
                        "filename": uploaded_file.name,
                        "model": selected_model,
                        "prompt": selected_prompt,
                        "result": result
                    })

st.divider()

# ==================== ANALYSIS HISTORY ====================

if 'analysis_history' in st.session_state and st.session_state.analysis_history:
    st.header("📜 Analysis History")
    
    for i, analysis in enumerate(reversed(st.session_state.analysis_history)):
        with st.expander(f"Analysis #{len(st.session_state.analysis_history) - i}: {analysis['filename']}"):
            st.markdown(f"**Model:** `{analysis['model']}`")
            st.markdown("**Prompt:**")
            st.text(analysis['prompt'])
            st.markdown("**Result:**")
            st.markdown(analysis['result'])

# ==================== FOOTER ====================

st.divider()

footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.caption("🤖 Powered by Groq Vision API")

with footer_col2:
    st.caption(f"📚 Model: {selected_model}")

with footer_col3:
    if st.button("🗑️ Clear History"):
        if 'analysis_history' in st.session_state:
            st.session_state.analysis_history = []
            st.rerun()

# ==================== EXAMPLE SECTION ====================

with st.expander("💡 Example Use Cases"):
    st.markdown("""
    ### Try these prompts:
    
    **For General Images:**
    - "Describe this image in detail"
    - "What objects can you see?"
    - "What is the main subject of this image?"
    
    **For Complaint Verification:**
    - "Is there any damage or broken equipment visible? Describe what you see."
    - "What issues or problems are visible in this image?"
    - "Does this image show infrastructure problems? Be specific."
    - "Analyze this for a maintenance complaint system"
    
    **For Text Recognition:**
    - "What text is visible in this image?"
    - "Read and transcribe any text you see"
    
    **For Quality Check:**
    - "Is this image clear or blurry?"
    - "Rate the quality of this image"
    - "Is there sufficient lighting in this image?"
    
    **For Spam Detection:**
    - "Is this appropriate for a complaint system?"
    - "Does this look like a legitimate photo or a meme?"
    - "Should this be flagged as spam?"
    """)

# ==================== TIPS ====================

with st.expander("📖 Tips for Best Results"):
    st.markdown("""
    ### Tips:
    
    ✅ **Upload clear, well-lit images**
    - Better lighting = better analysis
    - Avoid extremely dark or blurry photos
    
    ✅ **Be specific in your prompts**
    - "List all visible objects" is better than "What's here?"
    - "Describe any damage you see" is better than "Analyze this"
    
    ✅ **Supported formats**
    - JPG, JPEG, PNG, GIF, WebP
    - Max recommended size: 5MB
    
    ✅ **API Key**
    - Get free API key at https://console.groq.com
    - Set as environment variable: `GROQ_API_KEY=your_key_here`
    
    ✅ **Models**
    - **Llama 4 Scout**: Best for general vision tasks (recommended)
    - **Llama 4 Maverick**: Advanced reasoning capabilities
    """)

# ==================== API INFO ====================

with st.expander("🔧 API Information"):
    st.markdown(f"""
    ### Current Configuration
    
    **Model:** `{selected_model}`
    
    **Temperature:** 0.2 (more consistent)
    
    **Max Tokens:** 1000
    
    **Base URL:** https://api.groq.com/openai/v1/chat/completions
    
    ### Model Comparison
    
    | Model | Best For | Speed |
    |-------|----------|-------|
    | Llama 4 Scout | General vision, object detection | Fast |
    | Llama 4 Maverick | Complex reasoning, detailed analysis | Fast |
    
    ### Deprecated Models (Don't Use)
    - ❌ llama-3.2-90b-vision-preview
    - ❌ llama-3.2-11b-vision-preview
    - ❌ llava-v1.5-7b-4096-preview
    
    Use **Llama 4 Scout** instead!
    """)
