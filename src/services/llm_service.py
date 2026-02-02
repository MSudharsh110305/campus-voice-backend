"""
LLM service for Groq API integration.
Handles complaint categorization, rephrasing, spam detection, etc.
"""

import logging
import json
import asyncio
from typing import Dict, Optional, Any
from datetime import datetime
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
        prompt = self._build_categorization_prompt(text, context)
        
        try:
            start_time = datetime.utcnow()
            
            # Call Groq API (synchronous, so wrap in asyncio.to_thread)
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
                timeout=self.timeout
            )
            
            processing_time = (datetime.utcnow() - start_time).total_seconds() * 1000
            
            # Parse response
            content = response.choices[0].message.content
            result = json.loads(content)
            
            # Add metadata
            result["tokens_used"] = response.usage.total_tokens
            result["processing_time_ms"] = int(processing_time)
            result["model"] = self.model
            result["status"] = "Success"
            
            logger.info(f"Categorization successful: {result['category']}")
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response: {e}")
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
1. Hostel - Hostel facilities, cleanliness, room issues, mess complaints, amenities
2. General - Canteen, library, playground, common areas, campus facilities
3. Department - Academic issues, lab facilities, department infrastructure, faculty concerns
4. Disciplinary Committee - Ragging, harassment, bullying, serious violations, safety concerns

Task: Categorize this complaint into EXACTLY ONE category.

Also determine:
- Priority: Low, Medium, High, or Critical
- Is this complaint against an authority? (true/false)

Respond ONLY with valid JSON:
{{
  "category": "Hostel|General|Department|Disciplinary Committee",
  "priority": "Low|Medium|High|Critical",
  "reasoning": "Brief explanation (max 50 words)",
  "is_against_authority": false,
  "requires_image": false
}}

JSON Response:"""
    
    def _fallback_categorization(self, text: str) -> Dict[str, Any]:
        """Fallback categorization using keyword matching"""
        text_lower = text.lower()
        
        for category_info in CATEGORIES:
            keywords = category_info.get("keywords", [])
            if any(keyword in text_lower for keyword in keywords):
                return {
                    "category": category_info["name"],
                    "priority": "Medium",
                    "reasoning": "Keyword-based categorization (fallback)",
                    "is_against_authority": False,
                    "requires_image": False,
                    "status": "Fallback"
                }
        
        return {
            "category": "General",
            "priority": "Medium",
            "reasoning": "Default categorization (no keywords matched)",
            "is_against_authority": False,
            "requires_image": False,
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
            logger.info("Rephrasing successful")
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
- Structure with: Issue → Impact → Request
- Keep it under 200 words
- Maintain the original concern
- Do NOT add information not in the original
- Be respectful and professional

Rephrased Complaint:"""
    
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
        if len(text) < MIN_COMPLAINT_LENGTH:
            return {
                "is_spam": True,
                "confidence": 1.0,
                "reason": "Complaint too short"
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
            result = json.loads(content)
            
            logger.info(f"Spam detection: {result['is_spam']}")
            return result
            
        except Exception as e:
            logger.error(f"Spam detection error: {e}")
            return {
                "is_spam": False,
                "confidence": 0.5,
                "reason": "Unable to determine (error)"
            }
    
    def _build_spam_detection_prompt(self, text: str) -> str:
        """Build prompt for spam detection"""
        return f"""Detect if this complaint is spam, abusive, or not genuine.

Complaint Text:
"{text}"

Spam Indicators:
- Abusive or profane language
- No actual issue described
- Joke or prank complaint
- Repeated/duplicate content
- Personal attack on another student
- Test or dummy content

Respond ONLY with valid JSON:
{{
  "is_spam": true|false,
  "confidence": 0.0-1.0,
  "reason": "Brief explanation"
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
        
        Args:
            complaint_text: Complaint text
            image_description: Optional image description
        
        Returns:
            Dictionary with is_relevant, confidence, reason
        """
        # For now, simple heuristic
        # In production, use vision model or image analysis
        
        if not image_description:
            return {
                "is_relevant": True,
                "confidence": 0.7,
                "reason": "No image description provided, accepting by default"
            }
        
        # Check if description relates to complaint
        text_lower = complaint_text.lower()
        desc_lower = image_description.lower()
        
        common_words = set(text_lower.split()) & set(desc_lower.split())
        relevance_score = len(common_words) / max(len(text_lower.split()), 1)
        
        is_relevant = relevance_score > 0.1
        
        return {
            "is_relevant": is_relevant,
            "confidence": min(relevance_score * 2, 1.0),
            "reason": f"Found {len(common_words)} common keywords"
        }


# Create global instance
llm_service = LLMService()

__all__ = ["LLMService", "llm_service"]
