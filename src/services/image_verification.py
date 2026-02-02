"""
Image verification service using Groq Vision API.
"""

import logging
import base64
import asyncio
from typing import Dict, Any, Optional
from uuid import UUID
import httpx
from sqlalchemy.ext.asyncio import AsyncSession
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type

from groq import Groq
from src.config.settings import settings

logger = logging.getLogger(__name__)


class ImageVerificationService:
    """Service for image verification using Groq Vision API"""
    
    def __init__(self):
        """Initialize with Groq client"""
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        # ✅ Use latest Llama 4 Scout vision model (2026)
        self.vision_model = "meta-llama/llama-4-scout-17b-16e-instruct"
        self.temperature = 0.2  # Lower for consistent results
        self.max_tokens = 1000
    
    async def verify_image(
        self,
        db: AsyncSession,
        complaint_id: UUID,
        complaint_text: str,
        image_url: str,
        image_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify if image is relevant to complaint using Groq Vision API.
        
        Args:
            db: Database session
            complaint_id: Complaint UUID
            complaint_text: Complaint text
            image_url: Image URL (can be base64 or HTTP URL)
            image_description: Optional image description
        
        Returns:
            Verification result with is_relevant, confidence, reason
        """
        try:
            # Use LLM Vision to verify relevance
            result = await self.verify_image_relevance(
                complaint_text=complaint_text,
                image_url=image_url,
                image_description=image_description
            )
            
            # Log verification to database
            from src.database.models import ImageVerificationLog
            log = ImageVerificationLog(
                complaint_id=complaint_id,
                image_url=image_url,
                is_relevant=result["is_relevant"],
                confidence_score=result["confidence"],
                rejection_reason=result["reason"] if not result["is_relevant"] else None
            )
            db.add(log)
            await db.commit()
            
            logger.info(
                f"Image verification for {complaint_id}: "
                f"Relevant={result['is_relevant']}, Confidence={result['confidence']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Image verification error for {complaint_id}: {e}")
            # Fallback to accepting image if API fails
            return {
                "is_relevant": True,
                "confidence": 0.5,
                "reason": f"Verification error, accepted by default: {str(e)}",
                "status": "error"
            }
    
    @retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=2, max=30),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError))
    )
    async def verify_image_relevance(
        self,
        complaint_text: str,
        image_url: str,
        image_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify if image is relevant to complaint using Groq Vision API.
        
        Args:
            complaint_text: Complaint text
            image_url: Image URL or base64 data URI
            image_description: Optional image description
        
        Returns:
            Dictionary with is_relevant, confidence, reason, analysis
        """
        try:
            # Build verification prompt
            prompt = self._build_verification_prompt(complaint_text, image_description)
            
            # Prepare image data
            # Check if image_url is already a data URI
            if image_url.startswith("data:"):
                image_data_uri = image_url
            elif image_url.startswith("http"):
                # Download and encode if HTTP URL
                image_data_uri = await self._download_and_encode_image(image_url)
            else:
                # Assume it's a file path or base64 string
                logger.warning(f"Unsupported image URL format: {image_url[:50]}...")
                return self._fallback_verification(complaint_text, image_description)
            
            # Call Groq Vision API
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.vision_model,
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
                                    "url": image_data_uri
                                }
                            }
                        ]
                    }
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens
            )
            
            # Parse response
            content = response.choices[0].message.content
            
            # Extract JSON from response
            import json
            try:
                # Try to parse as JSON
                result = json.loads(content)
            except json.JSONDecodeError:
                # If not JSON, parse manually
                result = self._parse_vision_response(content, complaint_text)
            
            logger.info(
                f"Vision API verification: Relevant={result['is_relevant']}, "
                f"Confidence={result['confidence']}"
            )
            
            return result
            
        except Exception as e:
            logger.error(f"Groq Vision API error: {e}")
            return self._fallback_verification(complaint_text, image_description)
    
    def _build_verification_prompt(
        self,
        complaint_text: str,
        image_description: Optional[str]
    ) -> str:
        """Build prompt for image verification"""
        
        base_prompt = f"""You are an image verification system for a campus complaint management system.

**Complaint Text:**
"{complaint_text}"

{"**Image Description:** " + image_description if image_description else ""}

**Task:** Analyze the image and determine if it is RELEVANT and APPROPRIATE for this complaint.

**Evaluation Criteria:**

1. **Relevance** - Does the image show evidence related to the complaint?
   - Infrastructure/facilities mentioned in complaint
   - Damage, issues, or problems described
   - Related location or equipment

2. **Appropriateness** - Is the image suitable?
   - Not spam, memes, or unrelated screenshots
   - Not inappropriate or offensive content
   - Not a joke or test image
   - Genuine photo with clear subject

3. **Quality** - Can the issue be seen?
   - Sufficient clarity to see the problem
   - Adequate lighting
   - Focused on the relevant subject

**Your Response:**
Respond ONLY with valid JSON:

{{
  "is_relevant": true/false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation (max 100 words)",
  "detected_objects": ["list", "of", "visible", "objects"],
  "visible_issues": ["list", "of", "problems", "or", "none"],
  "quality_rating": "Good|Fair|Poor",
  "is_appropriate": true/false
}}

**Examples:**

Complaint: "Broken tap in hostel bathroom"
Image shows: Damaged faucet with water leaking
→ {{"is_relevant": true, "confidence": 0.95, "reason": "Image clearly shows broken tap matching complaint"}}

Complaint: "AC not working in lab"
Image shows: Meme or random screenshot
→ {{"is_relevant": false, "confidence": 0.9, "reason": "Image is a meme/screenshot, not genuine photo"}}

Analyze the provided image and respond with JSON:"""
        
        return base_prompt
    
    def _parse_vision_response(self, content: str, complaint_text: str) -> Dict[str, Any]:
        """Parse vision API response if not JSON"""
        
        content_lower = content.lower()
        
        # Determine relevance based on keywords
        relevant_indicators = [
            "relevant", "related", "shows", "visible", "matches",
            "appropriate", "genuine", "evidence", "depicts"
        ]
        
        irrelevant_indicators = [
            "not relevant", "irrelevant", "unrelated", "spam", "meme",
            "inappropriate", "not related", "doesn't match", "fake"
        ]
        
        # Calculate relevance
        relevant_count = sum(1 for word in relevant_indicators if word in content_lower)
        irrelevant_count = sum(1 for word in irrelevant_indicators if word in content_lower)
        
        is_relevant = relevant_count > irrelevant_count
        confidence = min((max(relevant_count, irrelevant_count) / 5.0), 1.0)
        
        return {
            "is_relevant": is_relevant,
            "confidence": confidence,
            "reason": content[:200] + "..." if len(content) > 200 else content,
            "detected_objects": [],
            "visible_issues": [],
            "quality_rating": "Unknown",
            "is_appropriate": is_relevant,
            "status": "parsed"
        }
    
    async def _download_and_encode_image(self, image_url: str) -> str:
        """Download image from URL and encode to base64 data URI"""
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(image_url)
                response.raise_for_status()
                
                # Get content type
                content_type = response.headers.get("content-type", "image/jpeg")
                
                # Encode to base64
                image_bytes = response.content
                base64_image = base64.b64encode(image_bytes).decode('utf-8')
                
                # Create data URI
                data_uri = f"data:{content_type};base64,{base64_image}"
                
                logger.info(f"Downloaded and encoded image from {image_url[:50]}...")
                return data_uri
                
        except Exception as e:
            logger.error(f"Failed to download image from {image_url}: {e}")
            raise
    
    def _fallback_verification(
        self,
        complaint_text: str,
        image_description: Optional[str]
    ) -> Dict[str, Any]:
        """
        Fallback verification using keyword matching.
        Used when Vision API fails.
        """
        
        if not image_description:
            # No description, accept by default
            return {
                "is_relevant": True,
                "confidence": 0.6,
                "reason": "No image description provided, accepting by default (Vision API unavailable)",
                "detected_objects": [],
                "visible_issues": [],
                "quality_rating": "Unknown",
                "is_appropriate": True,
                "status": "fallback"
            }
        
        # Check if description relates to complaint
        text_lower = complaint_text.lower()
        desc_lower = image_description.lower()
        
        # Find common words
        text_words = set(text_lower.split())
        desc_words = set(desc_lower.split())
        common_words = text_words & desc_words
        
        # Remove common stopwords
        stopwords = {"the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "with"}
        common_words = common_words - stopwords
        
        # Calculate relevance score
        relevance_score = len(common_words) / max(len(text_words), 1)
        is_relevant = relevance_score > 0.1
        
        return {
            "is_relevant": is_relevant,
            "confidence": min(relevance_score * 2, 1.0),
            "reason": f"Keyword matching: Found {len(common_words)} common keywords (Vision API fallback)",
            "detected_objects": list(common_words),
            "visible_issues": [],
            "quality_rating": "Unknown",
            "is_appropriate": is_relevant,
            "status": "fallback"
        }
    
    def encode_uploaded_file_to_data_uri(
        self,
        file_bytes: bytes,
        mime_type: str = "image/jpeg"
    ) -> str:
        """
        Encode uploaded file bytes to base64 data URI.
        
        Args:
            file_bytes: Image file bytes
            mime_type: MIME type (e.g., "image/jpeg", "image/png")
        
        Returns:
            Data URI string
        """
        base64_image = base64.b64encode(file_bytes).decode('utf-8')
        return f"data:{mime_type};base64,{base64_image}"


# Create global instance
image_verification_service = ImageVerificationService()

__all__ = ["ImageVerificationService", "image_verification_service"]
