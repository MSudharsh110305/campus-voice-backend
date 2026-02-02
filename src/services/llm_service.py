"""
LLM service for Groq API integration.
Handles complaint categorization, rephrasing, spam detection, etc.
"""

import logging
import json
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime, timezone
import httpx
from tenacity import (
    retry,
    stop_after_attempt,
    wait_exponential,
    retry_if_exception_type
)

from groq import Groq
from src.config.settings import settings
from src.config.constants import CATEGORIES, MIN_COMPLAINT_LENGTH

logger = logging.getLogger(__name__)


class LLMService:
    """Service for LLM operations using Groq API"""
    
    def __init__(self):
        """Initialize LLM service with Groq client"""
        self.groq_client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.timeout = settings.LLM_TIMEOUT
        logger.info(f"LLM Service initialized with model: {self.model}")
    
    # ==================== CATEGORIZATION ====================
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError))
    )
    async def categorize_complaint(
        self,
        text: str,
        context: Dict[str, str]
    ) -> Dict[str, Any]:
        """
        Categorize complaint using LLM.
        
        Args:
            text: Complaint text
            context: Student context (gender, stay_type, department)
        
        Returns:
            Dictionary with category, priority, reasoning
        """
        if not text or len(text.strip()) < MIN_COMPLAINT_LENGTH:
            logger.warning("Text too short for categorization")
            return self._fallback_categorization(text)
        
        prompt = self._build_categorization_prompt(text, context)
        
        try:
            # ✅ FIXED: Use timezone-aware datetime
            start_time = datetime.now(timezone.utc)
            
            # Call Groq API (synchronous, so wrap in asyncio.to_thread)
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            processing_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            # Parse response
            content = response.choices[0].message.content
            
            # Try to extract JSON from response
            result = self._extract_json_from_response(content)
            
            if not result:
                logger.warning("Failed to parse LLM response as JSON, using fallback")
                return self._fallback_categorization(text)
            
            # Validate result
            if not self._validate_categorization_result(result):
                logger.warning("Invalid categorization result, using fallback")
                return self._fallback_categorization(text)
            
            # Add metadata
            result["tokens_used"] = response.usage.total_tokens
            result["processing_time_ms"] = int(processing_time)
            result["model"] = self.model
            result["status"] = "Success"
            
            logger.info(
                f"Categorization successful: {result['category']} "
                f"(Priority: {result['priority']}, Tokens: {result['tokens_used']})"
            )
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._fallback_categorization(text)
        except Exception as e:
            logger.error(f"LLM categorization error: {e}")
            return self._fallback_categorization(text)
    
    def _build_categorization_prompt(self, text: str, context: Dict[str, str]) -> str:
        """Build prompt for categorization"""
        return f"""You are a complaint categorization system for a campus grievance portal.

Student Profile:
- Gender: {context.get('gender', 'Unknown')}
- Residence Type: {context.get('stay_type', 'Unknown')}
- Department: {context.get('department', 'Unknown')}

Complaint Text:
"{text}"

Categories:
1. **Hostel** - Hostel facilities, cleanliness, room issues, mess complaints, hostel amenities, water supply, electricity in hostel
2. **General** - Canteen, library, playground, common areas, campus facilities, transport, parking
3. **Department** - Academic issues, lab facilities, department infrastructure, classroom issues, equipment problems
4. **Disciplinary Committee** - Ragging, harassment, bullying, serious violations, safety concerns, threats

Task: Categorize this complaint into EXACTLY ONE category.

Priority Levels:
- **Low**: Minor inconvenience, cosmetic issues
- **Medium**: Moderate impact, needs attention soon
- **High**: Significant impact, urgent attention needed
- **Critical**: Safety concern, immediate action required

Also determine:
- Is this complaint against an authority/staff member? (true/false)
- Does this complaint require image evidence? (true/false)

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "category": "Hostel|General|Department|Disciplinary Committee",
  "priority": "Low|Medium|High|Critical",
  "reasoning": "Brief explanation (max 50 words)",
  "is_against_authority": false,
  "requires_image": false
}}

JSON Response:"""
    
    def _extract_json_from_response(self, content: str) -> Optional[Dict[str, Any]]:
        """Extract JSON from LLM response (handles markdown code blocks)"""
        try:
            # Try direct JSON parse first
            return json.loads(content)
        except json.JSONDecodeError:
            # Try to extract JSON from markdown code blocks
            import re
            
            # Remove markdown code blocks
            json_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
            match = re.search(json_pattern, content, re.DOTALL)
            
            if match:
                try:
                    return json.loads(match.group(1))
                except json.JSONDecodeError:
                    pass
            
            # Try to find JSON object in text
            json_pattern = r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}'
            match = re.search(json_pattern, content, re.DOTALL)
            
            if match:
                try:
                    return json.loads(match.group(0))
                except json.JSONDecodeError:
                    pass
            
            return None
    
    def _validate_categorization_result(self, result: Dict[str, Any]) -> bool:
        """Validate categorization result structure"""
        required_fields = ["category", "priority"]
        
        if not all(field in result for field in required_fields):
            return False
        
        valid_categories = ["Hostel", "General", "Department", "Disciplinary Committee"]
        valid_priorities = ["Low", "Medium", "High", "Critical"]
        
        if result["category"] not in valid_categories:
            return False
        
        if result["priority"] not in valid_priorities:
            return False
        
        return True
    
    def _fallback_categorization(self, text: str) -> Dict[str, Any]:
        """Fallback categorization using keyword matching"""
        text_lower = text.lower()
        
        # Keyword-based categorization
        category_keywords = {
            "Hostel": ["hostel", "room", "mess", "warden", "dorm", "hostel", "bed", "bathroom", "water supply", "electricity", "ac", "fan"],
            "Department": ["lab", "classroom", "department", "academic", "faculty", "professor", "teacher", "lecture", "course", "exam", "lab equipment"],
            "Disciplinary Committee": ["ragging", "harassment", "bullying", "threat", "abuse", "safety", "assault", "violence", "discrimination"],
            "General": ["canteen", "library", "playground", "ground", "parking", "transport", "bus", "wifi", "internet", "campus"]
        }
        
        # Count keyword matches for each category
        category_scores = {}
        for category, keywords in category_keywords.items():
            score = sum(1 for keyword in keywords if keyword in text_lower)
            if score > 0:
                category_scores[category] = score
        
        # Select category with highest score
        if category_scores:
            selected_category = max(category_scores, key=category_scores.get)
        else:
            selected_category = "General"
        
        # Determine priority based on urgency keywords
        urgency_keywords = {
            "Critical": ["emergency", "urgent", "immediate", "critical", "dangerous", "unsafe"],
            "High": ["broken", "not working", "damaged", "leaking", "problem"],
            "Medium": ["issue", "concern", "needs", "improve"],
            "Low": ["suggestion", "request", "minor"]
        }
        
        selected_priority = "Medium"
        for priority, keywords in urgency_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                selected_priority = priority
                break
        
        logger.info(f"Fallback categorization: {selected_category} (Priority: {selected_priority})")
        
        return {
            "category": selected_category,
            "priority": selected_priority,
            "reasoning": "Keyword-based categorization (LLM fallback)",
            "is_against_authority": any(word in text_lower for word in ["faculty", "teacher", "professor", "staff", "warden", "hod"]),
            "requires_image": any(word in text_lower for word in ["broken", "damaged", "leaking", "dirty"]),
            "status": "Fallback"
        }
    
    # ==================== REPHRASING ====================
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError))
    )
    async def rephrase_complaint(self, text: str) -> str:
        """
        Rephrase complaint to be professional and clear.
        
        Args:
            text: Original complaint text
        
        Returns:
            Rephrased text
        """
        if not text or len(text.strip()) < 10:
            logger.warning("Text too short for rephrasing, returning original")
            return text
        
        prompt = self._build_rephrasing_prompt(text)
        
        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower for more consistent rephrasing
                max_tokens=400,
                timeout=self.timeout
            )
            
            rephrased = response.choices[0].message.content.strip()
            
            # Remove any markdown formatting
            rephrased = rephrased.replace("**", "").replace("*", "")
            
            # If rephrased text is too short or looks invalid, return original
            if len(rephrased) < 20 or rephrased.startswith("Error"):
                logger.warning("Rephrased text looks invalid, returning original")
                return text
            
            logger.info(f"Rephrasing successful (Original: {len(text)} chars → Rephrased: {len(rephrased)} chars)")
            return rephrased
            
        except Exception as e:
            logger.error(f"LLM rephrasing error: {e}")
            return text  # Return original if rephrasing fails
    
    def _build_rephrasing_prompt(self, text: str) -> str:
        """Build prompt for rephrasing"""
        return f"""Rephrase this student complaint to be professional, clear, and concise while preserving all key information.

Original Complaint:
"{text}"

Guidelines:
- Remove slang and informal language
- Fix grammar and spelling errors
- Structure with: Issue → Impact → Request/Expectation
- Keep it under 200 words
- Maintain the original concern and all important details
- Do NOT add information not in the original
- Be respectful and professional
- Use active voice
- Be specific and factual

Provide ONLY the rephrased complaint text (no explanations, no labels):"""
    
    # ==================== SPAM DETECTION ====================
    
    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError))
    )
    async def detect_spam(self, text: str) -> Dict[str, Any]:
        """
        Detect if complaint is spam or abusive.
        
        Args:
            text: Complaint text
        
        Returns:
            Dictionary with is_spam, confidence, reason
        """
        # Quick checks first
        if len(text.strip()) < MIN_COMPLAINT_LENGTH:
            return {
                "is_spam": True,
                "confidence": 1.0,
                "reason": f"Complaint too short (minimum {MIN_COMPLAINT_LENGTH} characters required)"
            }
        
        # Check for test/dummy content
        test_phrases = ["test", "testing", "asdf", "qwerty", "dummy", "sample"]
        if any(phrase in text.lower() for phrase in test_phrases) and len(text) < 50:
            return {
                "is_spam": True,
                "confidence": 0.9,
                "reason": "Appears to be test/dummy content"
            }
        
        prompt = self._build_spam_detection_prompt(text)
        
        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower for more consistent detection
                max_tokens=200,
                timeout=self.timeout
            )
            
            content = response.choices[0].message.content
            result = self._extract_json_from_response(content)
            
            if not result or "is_spam" not in result:
                logger.warning("Invalid spam detection response, assuming not spam")
                return {
                    "is_spam": False,
                    "confidence": 0.5,
                    "reason": "Unable to determine (invalid response)"
                }
            
            logger.info(f"Spam detection: {result['is_spam']} (Confidence: {result.get('confidence', 'N/A')})")
            return result
            
        except Exception as e:
            logger.error(f"Spam detection error: {e}")
            # Default to not spam on error (better UX than blocking legitimate complaints)
            return {
                "is_spam": False,
                "confidence": 0.5,
                "reason": "Unable to determine (API error)"
            }
    
    def _build_spam_detection_prompt(self, text: str) -> str:
        """Build prompt for spam detection"""
        return f"""Detect if this complaint is spam, abusive, or not genuine.

Complaint Text:
"{text}"

Spam Indicators:
- Abusive, profane, or offensive language
- No actual issue or concern described
- Joke, prank, or sarcastic complaint
- Repeated gibberish or random characters
- Personal attack targeting specific individuals by name
- Test or dummy content (e.g., "test", "asdf")
- Advertisement or promotional content
- Completely irrelevant to campus issues

NOT Spam:
- Valid concerns expressed with emotion or frustration
- Complaints mentioning authorities in professional context
- Legitimate issues with informal language
- Constructive criticism

Respond ONLY with valid JSON (no markdown):
{{
  "is_spam": true|false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation (max 30 words)"
}}

JSON Response:"""
    
    # ==================== IMAGE VERIFICATION ====================
    
    async def verify_image_relevance(
        self,
        complaint_text: str,
        image_description: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Verify if image is relevant to complaint.
        
        NOTE: This is a basic heuristic implementation.
        For production, use the image_verification_service.py with Groq Vision API.
        
        Args:
            complaint_text: Complaint text
            image_description: Optional image description
        
        Returns:
            Dictionary with is_relevant, confidence, reason
        """
        if not image_description:
            return {
                "is_relevant": True,
                "confidence": 0.7,
                "reason": "No image description provided, accepting by default"
            }
        
        # Check if description relates to complaint
        text_lower = complaint_text.lower()
        desc_lower = image_description.lower()
        
        # Remove common stopwords
        stopwords = {"the", "a", "an", "is", "in", "on", "at", "to", "for", "of", "with", "and", "or", "but"}
        text_words = set(text_lower.split()) - stopwords
        desc_words = set(desc_lower.split()) - stopwords
        
        # Find common meaningful words
        common_words = text_words & desc_words
        
        # Calculate relevance score
        if len(text_words) == 0:
            relevance_score = 0
        else:
            relevance_score = len(common_words) / len(text_words)
        
        is_relevant = relevance_score > 0.1 or len(common_words) >= 2
        
        confidence = min(relevance_score * 2, 1.0)
        if len(common_words) >= 3:
            confidence = max(confidence, 0.8)
        
        logger.info(f"Image relevance: {is_relevant} (Confidence: {confidence:.2f}, Common words: {len(common_words)})")
        
        return {
            "is_relevant": is_relevant,
            "confidence": confidence,
            "reason": f"Found {len(common_words)} common keywords between complaint and image description"
        }
    
    # ==================== UTILITY METHODS ====================
    
    def get_service_stats(self) -> Dict[str, Any]:
        """
        Get LLM service statistics and configuration.
        
        Returns:
            Service statistics
        """
        return {
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout": self.timeout,
            "max_retries": settings.LLM_MAX_RETRIES,
            "status": "operational"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Groq API connection.
        
        Returns:
            Connection test result
        """
        try:
            # ✅ Use timezone-aware datetime
            start_time = datetime.now(timezone.utc)
            
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": "Reply with: OK"}],
                temperature=0,
                max_tokens=10,
                timeout=5
            )
            
            response_time = (datetime.now(timezone.utc) - start_time).total_seconds() * 1000
            
            return {
                "status": "success",
                "model": self.model,
                "response_time_ms": int(response_time),
                "message": "Groq API connection successful"
            }
            
        except Exception as e:
            logger.error(f"Groq API connection test failed: {e}")
            return {
                "status": "error",
                "model": self.model,
                "message": f"Connection failed: {str(e)}"
            }


# Create global instance
llm_service = LLMService()

__all__ = ["LLMService", "llm_service"]
