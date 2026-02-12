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
        """Initialize LLM service with Groq client.

        Gracefully handles missing GROQ_API_KEY by setting client to None.
        All LLM methods fall back to keyword-based logic when the client
        is unavailable.
        """
        self.groq_client = None
        self.model = settings.LLM_MODEL
        self.temperature = settings.LLM_TEMPERATURE
        self.max_tokens = settings.LLM_MAX_TOKENS
        self.timeout = settings.LLM_TIMEOUT

        api_key = settings.GROQ_API_KEY
        if api_key and api_key.strip():
            try:
                self.groq_client = Groq(api_key=api_key)
                logger.info(f"LLM Service initialized with model: {self.model}")
            except Exception as e:
                logger.warning(f"Failed to initialize Groq client: {e}. LLM features will use fallback logic.")
        else:
            logger.warning("GROQ_API_KEY is not set. LLM features will use keyword-based fallback logic.")
    
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
            return self._fallback_categorization(text, context)

        if not self.groq_client:
            logger.info("Groq client unavailable, using fallback categorization")
            return self._fallback_categorization(text, context)

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
                return self._fallback_categorization(text, context)
            
            # Validate result
            if not self._validate_categorization_result(result):
                logger.warning("Invalid categorization result, using fallback")
                return self._fallback_categorization(text, context)

            # Ensure target_department is present (fallback to student's department)
            if "target_department" not in result or not result["target_department"]:
                result["target_department"] = context.get("department", "CSE")
                logger.info(f"No target_department in LLM response, using student's department: {result['target_department']}")

            # Ensure confidence is present
            if "confidence" not in result:
                result["confidence"] = 0.8  # Default confidence for successful LLM response

            # Add metadata
            result["tokens_used"] = response.usage.total_tokens
            result["processing_time_ms"] = int(processing_time)
            result["model"] = self.model
            result["status"] = "Success"

            logger.info(
                f"Categorization successful: {result['category']} "
                f"(Priority: {result['priority']}, Target Dept: {result['target_department']}, "
                f"Confidence: {result.get('confidence', 'N/A')}, Tokens: {result['tokens_used']})"
            )
            return result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse LLM response as JSON: {e}")
            return self._fallback_categorization(text, context)
        except Exception as e:
            logger.error(f"LLM categorization error: {e}")
            return self._fallback_categorization(text, context)
    
    def _build_categorization_prompt(self, text: str, context: Dict[str, str]) -> str:
        """Build prompt for categorization with department detection"""
        gender = context.get('gender', 'Unknown')
        stay_type = context.get('stay_type', 'Unknown')
        department = context.get('department', 'Unknown')

        return f"""You are a complaint categorization and department routing system for SREC college campus.

Student Profile:
- Gender: {gender}
- Residence Type: {stay_type}
- Department: {department}

Complaint Text:
"{text}"

Categories (choose EXACTLY ONE):
1. **Men's Hostel** - Hostel room, mess food, hostel bathroom, water supply, hostel electricity, hostel cleanliness, hostel amenities. ONLY for Male Hostel students.
2. **Women's Hostel** - Hostel room, mess food, hostel bathroom, water supply, hostel electricity, hostel cleanliness, hostel amenities. ONLY for Female Hostel students.
3. **General** - Campus infrastructure and physical facilities ONLY: canteen, library, playground, parking, transport, gym, auditorium, campus buildings, roads, drinking water stations, common area furniture, campus wifi/internet.
4. **Department** - Academic and department-specific: lab equipment, classroom issues, faculty/teaching concerns, timetable, curriculum, exam issues, project/internship, department infrastructure.
5. **Disciplinary Committee** - Ragging, harassment, bullying, threats, violence, abuse, serious misconduct, safety concerns.

STRICT CATEGORIZATION RULES:
- If Gender is "Male" and complaint is about hostel facilities/issues, choose "Men's Hostel".
- If Gender is "Female" and complaint is about hostel facilities/issues, choose "Women's Hostel".
- "General" = physical infrastructure and materialistic issues on campus (NOT academic, NOT hostel).
- "Department" = academic, faculty, lab, classroom, course-related issues.
- Only use "Disciplinary Committee" for serious safety/harassment/ragging issues.
- Categorize based on complaint content, not student eligibility (validation happens separately).

DEPARTMENT DETECTION (Analyze complaint text for department keywords):
Valid Departments: CSE, ECE, MECH, CIVIL, EEE, IT, BIO, AERO, RAA, EIE, MBA, AIDS, MTECH_CSE

Rules:
- If complaint mentions specific department keywords (e.g., "ECE lab", "mechanical workshop", "CSE faculty"), set target_department to that department code
- If no specific department mentioned, use student's department ({department})
- For cross-department complaints (student from one dept complaining about another), target the mentioned department
- Examples:
  * "The ECE lab equipment is broken" from CSE student → target_department: "ECE"
  * "Our classroom projector is not working" from ECE student → target_department: "ECE"
  * "The mechanical workshop is too noisy" from CSE student → target_department: "MECH"

Priority Levels:
- **Low**: Minor inconvenience, cosmetic issues
- **Medium**: Moderate impact, needs attention soon
- **High**: Significant impact, urgent attention needed
- **Critical**: Safety concern, immediate action required

Respond ONLY with valid JSON (no markdown, no code blocks):
{{
  "category": "Men's Hostel|Women's Hostel|General|Department|Disciplinary Committee",
  "target_department": "CSE|ECE|MECH|CIVIL|EEE|IT|BIO|AERO|RAA|EIE|MBA|AIDS|MTECH_CSE",
  "priority": "Low|Medium|High|Critical",
  "reasoning": "Brief explanation (max 50 words)",
  "confidence": 0.0-1.0,
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
        
        valid_categories = ["Men's Hostel", "Women's Hostel", "General", "Department", "Disciplinary Committee"]
        valid_priorities = ["Low", "Medium", "High", "Critical"]
        
        if result["category"] not in valid_categories:
            return False
        
        if result["priority"] not in valid_priorities:
            return False
        
        return True
    
    def _fallback_categorization(self, text: str, context: Optional[Dict[str, str]] = None) -> Dict[str, Any]:
        """Fallback categorization using keyword matching with student context and department detection"""
        text_lower = text.lower()

        # Keyword-based categorization
        category_keywords = {
            "Hostel": ["hostel", "room", "mess", "warden", "dorm", "bed", "bathroom", "water supply", "electricity", "ac", "fan"],
            "Department": ["lab", "classroom", "department", "academic", "faculty", "professor", "teacher", "lecture", "course", "exam", "lab equipment"],
            "Disciplinary Committee": ["ragging", "harassment", "bullying", "threat", "abuse", "safety", "assault", "violence", "discrimination"],
            "General": ["canteen", "library", "playground", "ground", "parking", "transport", "bus", "wifi", "internet", "campus", "infrastructure"]
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

        # Map generic "Hostel" to gender-specific category using student context
        # ✅ FIXED: Don't pre-filter by stay_type - let validation in complaint_service reject invalid submissions
        if selected_category == "Hostel":
            if context:
                gender = context.get("gender", "")
                # Map to gender-specific hostel category (validation will reject if Day Scholar)
                if gender == "Female":
                    selected_category = "Women's Hostel"
                else:
                    selected_category = "Men's Hostel"
            else:
                selected_category = "Men's Hostel"

        # ✅ NEW: Department detection using keywords
        department_keywords = {
            "CSE": ["cse", "computer science", "computer lab", "cs department"],
            "ECE": ["ece", "electronics", "communication", "ec department"],
            "MECH": ["mech", "mechanical", "workshop", "machine"],
            "CIVIL": ["civil", "construction", "surveying"],
            "EEE": ["eee", "electrical", "power", "circuits"],
            "IT": ["it", "information technology", "it lab"],
            "BIO": ["bio", "biomedical", "biomed"],
            "AERO": ["aero", "aeronautical", "aerospace"],
            "RAA": ["raa", "robotics", "automation"],
            "EIE": ["eie", "instrumentation"],
            "MBA": ["mba", "management"],
            "AIDS": ["aids", "ai", "data science", "artificial intelligence"],
            "MTECH_CSE": ["mtech", "m.tech"]
        }

        # Detect target department from complaint text
        detected_department = None
        for dept_code, keywords in department_keywords.items():
            if any(keyword in text_lower for keyword in keywords):
                detected_department = dept_code
                break

        # Fallback to student's department if no department detected
        target_department = detected_department or (context.get("department", "CSE") if context else "CSE")

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

        logger.info(
            f"Fallback categorization: {selected_category} (Priority: {selected_priority}, "
            f"Target Dept: {target_department})"
        )

        return {
            "category": selected_category,
            "target_department": target_department,
            "priority": selected_priority,
            "reasoning": "Keyword-based categorization (LLM fallback)",
            "confidence": 0.5,  # Lower confidence for fallback
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

        if not self.groq_client:
            logger.info("Groq client unavailable, skipping rephrasing")
            return text

        prompt = self._build_rephrasing_prompt(text)
        
        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,  # Lower for more consistent rephrasing
                max_tokens=200,
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
        return f"""Rephrase this student complaint into 1-2 short, clear sentences. Keep the original meaning intact.

Original:
"{text}"

Rules:
- Output 1-2 concise sentences ONLY (max 50 words)
- Preserve the core issue and key details
- Fix grammar and spelling
- Keep it natural and professional
- Do NOT add new information
- Do NOT use bullet points or structured format
- Do NOT start with "The student" or "I would like to"

Provide ONLY the rephrased text:"""
    
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
        
        if not self.groq_client:
            logger.info("Groq client unavailable, skipping LLM spam detection (assuming not spam)")
            return {
                "is_spam": False,
                "confidence": 0.5,
                "reason": "LLM unavailable, skipping spam detection"
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
    
    # ==================== IMAGE REQUIREMENT DETECTION ====================

    @retry(
        stop=stop_after_attempt(settings.LLM_MAX_RETRIES),
        wait=wait_exponential(multiplier=1, min=1, max=60),
        retry=retry_if_exception_type((httpx.HTTPError, TimeoutError))
    )
    async def check_image_requirement(
        self,
        complaint_text: str,
        category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Determine if complaint requires image evidence using LLM.

        Args:
            complaint_text: Complaint text to analyze
            category: Optional category hint

        Returns:
            Dictionary with image_required, reasoning, confidence
        """
        if not complaint_text or len(complaint_text.strip()) < MIN_COMPLAINT_LENGTH:
            logger.warning("Text too short for image requirement check")
            return {
                "image_required": False,
                "reasoning": "Complaint text too short to analyze",
                "confidence": 0.5
            }

        if not self.groq_client:
            logger.info("Groq client unavailable, using fallback image requirement check")
            return self._fallback_image_requirement(complaint_text)

        prompt = self._build_image_requirement_prompt(complaint_text, category)

        try:
            response = await asyncio.to_thread(
                self.groq_client.chat.completions.create,
                model=self.model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.2,  # Lower for more consistent decisions
                max_tokens=300,
                timeout=self.timeout
            )

            content = response.choices[0].message.content
            result = self._extract_json_from_response(content)

            if not result or "image_required" not in result:
                logger.warning("Invalid image requirement response, using fallback")
                return self._fallback_image_requirement(complaint_text)

            logger.info(
                f"Image requirement check: {result['image_required']} "
                f"(Confidence: {result.get('confidence', 'N/A')})"
            )
            return result

        except Exception as e:
            logger.error(f"Image requirement check error: {e}")
            return self._fallback_image_requirement(complaint_text)

    def _build_image_requirement_prompt(self, text: str, category: Optional[str]) -> str:
        """Build prompt for image requirement detection"""
        category_hint = f"\nCategory: {category}" if category else ""

        return f"""Analyze this complaint and determine if visual evidence (images/photos) is REQUIRED for proper verification and resolution.

Complaint Text:
"{text}"{category_hint}

Image is REQUIRED for:
- Infrastructure issues (broken/damaged items, leaks, structural problems)
- Cleanliness issues (dirty areas, unhygienic conditions)
- Equipment malfunction (visible damage or defects)
- Safety hazards (exposed wires, broken furniture, hazardous conditions)
- Facility problems (broken doors, windows, cracks, stains)
- Visible proof needed (graffiti, unauthorized items, visible violations)

Image is OPTIONAL/NOT REQUIRED for:
- Abstract/policy issues (rules, procedures, timings)
- Service-related complaints (staff behavior, response time)
- Academic issues (course content, faculty concerns)
- Request for improvements (suggestions without specific issues)
- Abstract concerns (noise, temperature preferences without visible cause)
- Personal issues (interpersonal conflicts, requests)

Task: Determine if this complaint REQUIRES image evidence.

Respond ONLY with valid JSON (no markdown):
{{
  "image_required": true|false,
  "reasoning": "Brief explanation why image is/isn't required (max 50 words)",
  "confidence": 0.0-1.0,
  "suggested_evidence": "What the image should show (only if required)"
}}

JSON Response:"""

    def _fallback_image_requirement(self, text: str) -> Dict[str, Any]:
        """Fallback logic for image requirement detection"""
        text_lower = text.lower()

        # Keywords that typically require visual evidence
        requires_image_keywords = [
            "broken", "damaged", "leaking", "leak", "dirty", "filthy", "stain",
            "crack", "torn", "not working", "malfunctioning", "defective",
            "unhygienic", "unclean", "blocked", "clogged", "rusty", "peeling",
            "exposed wire", "hanging", "falling", "detached", "missing",
            "visible", "see", "look", "show", "picture", "photo"
        ]

        # Count matches
        matches = sum(1 for keyword in requires_image_keywords if keyword in text_lower)

        # Determine if image is required
        image_required = matches >= 2  # At least 2 strong indicators
        confidence = min(0.5 + (matches * 0.1), 0.9)

        logger.info(
            f"Fallback image requirement: {image_required} "
            f"(Matches: {matches}, Confidence: {confidence:.2f})"
        )

        return {
            "image_required": image_required,
            "reasoning": f"Keyword-based analysis detected {matches} visual problem indicators" if image_required else "No strong visual evidence requirements detected",
            "confidence": confidence,
            "suggested_evidence": "Photo showing the issue clearly" if image_required else None
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
            "status": "operational" if self.groq_client else "fallback_mode"
        }
    
    async def test_connection(self) -> Dict[str, Any]:
        """
        Test Groq API connection.

        Returns:
            Connection test result
        """
        if not self.groq_client:
            return {
                "status": "unavailable",
                "model": self.model,
                "message": "Groq client not initialized (API key missing or invalid)"
            }

        try:
            # Use timezone-aware datetime
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
