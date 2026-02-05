"""
Complaint service with main business logic.

✅ UPDATED: Binary image storage support
✅ UPDATED: Image verification integration
✅ UPDATED: No image_url field usage
"""

import logging
from typing import Optional, Dict, Any, List
from uuid import UUID
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import UploadFile

from src.database.models import Complaint, Student, ComplaintCategory, StatusUpdate
from src.repositories.complaint_repo import ComplaintRepository
from src.repositories.student_repo import StudentRepository
from src.services.llm_service import llm_service
from src.services.authority_service import authority_service
from src.services.notification_service import notification_service
from src.services.spam_detection import spam_detection_service
from src.services.image_verification import image_verification_service
from src.utils.file_upload import file_upload_handler
from src.config.constants import PRIORITY_SCORES

logger = logging.getLogger(__name__)


class ComplaintService:
    """Service for complaint operations"""
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.complaint_repo = ComplaintRepository(db)
        self.student_repo = StudentRepository(db)
    
    async def create_complaint(
        self,
        student_roll_no: str,
        category_id: int,
        original_text: str,
        visibility: str = "Public",
        image_file: Optional[UploadFile] = None  # ✅ NEW: Accept UploadFile
    ) -> Dict[str, Any]:
        """
        Create a new complaint with full LLM processing and optional image.

        ✅ UPDATED: Accepts image_file (UploadFile) instead of image_url
        ✅ UPDATED: Implements spam rejection (doesn't create complaint if spam)
        ✅ UPDATED: Enforces image requirement via LLM

        Args:
            student_roll_no: Student roll number
            category_id: Category ID
            original_text: Original complaint text
            visibility: Visibility level (Public, Private, Anonymous)
            image_file: Optional uploaded image file

        Returns:
            Dictionary with complaint details and image verification results

        Raises:
            ValueError: If spam detected or required image missing
        """
        # Get student with department
        student = await self.student_repo.get_with_department(student_roll_no)
        if not student:
            raise ValueError("Student not found")

        if not student.is_active:
            raise ValueError("Student account is inactive")

        # ✅ FIXED: Check spam blacklist
        blacklist_check = await spam_detection_service.check_spam_blacklist(
            self.db, student_roll_no
        )
        if blacklist_check["is_blacklisted"]:
            error_msg = f"Account suspended: {blacklist_check['reason']}."
            if blacklist_check.get('is_permanent'):
                error_msg += " This is a permanent ban."
            elif blacklist_check.get('expires_at'):
                error_msg += f" Ban expires on {blacklist_check['expires_at']}."

            logger.warning(f"Blacklisted user {student_roll_no} attempted to create complaint")
            raise ValueError(error_msg)

        # Build context for LLM
        context = {
            "gender": student.gender or "Unknown",
            "stay_type": student.stay_type or "Unknown",
            "department": student.department.code if (student.department and hasattr(student.department, 'code')) else "Unknown"
        }

        # LLM Processing
        logger.info(f"Processing complaint for {student_roll_no}")

        try:
            # 1. Check for spam FIRST (before processing)
            spam_check = await llm_service.detect_spam(original_text)

            # ✅ NEW: REJECT spam complaints outright (don't create)
            if spam_check.get("is_spam"):
                spam_reason = spam_check.get("reason", "Content flagged as spam or abusive")
                logger.warning(
                    f"Spam complaint rejected for {student_roll_no}: {spam_reason}"
                )

                # Log spam attempt for monitoring (optional)
                spam_count = await spam_detection_service.get_spam_count(
                    self.db, student_roll_no
                )

                # If multiple spam attempts, consider blacklisting
                if spam_count >= 3:
                    await spam_detection_service.add_to_blacklist(
                        db=self.db,
                        student_roll_no=student_roll_no,
                        reason=f"Multiple spam attempts ({spam_count + 1} total)",
                        is_permanent=False,
                        ban_duration_days=7
                    )
                    error_msg = f"Complaint marked as spam/abusive: {spam_reason}. Account temporarily suspended due to multiple violations."
                else:
                    error_msg = f"Complaint marked as spam/abusive: {spam_reason}"

                # ✅ CRITICAL: Raise error (don't create complaint)
                raise ValueError(error_msg)

            # 2. Categorize and get priority
            categorization = await llm_service.categorize_complaint(original_text, context)

            # 3. Rephrase for professionalism
            rephrased_text = await llm_service.rephrase_complaint(original_text)

            # ✅ NEW: 4. Check if image is REQUIRED for this complaint
            image_requirement = await llm_service.check_image_requirement(
                complaint_text=original_text,
                category=categorization.get("category")
            )

            # ✅ NEW: Enforce image requirement
            if image_requirement.get("image_required") and not image_file:
                reason = image_requirement.get("reasoning", "Visual evidence required")
                suggested = image_requirement.get("suggested_evidence", "relevant photo")
                error_msg = (
                    f"This complaint requires supporting images. {reason}. "
                    f"Please upload at least one image showing {suggested}."
                )
                logger.warning(f"Image required but not provided for {student_roll_no}: {reason}")
                raise ValueError(error_msg)

        except ValueError:
            # Re-raise ValueError (spam rejection or missing image)
            raise
        except Exception as e:
            logger.error(f"LLM processing error: {e}")
            # Fallback values
            categorization = {
                "category": "General",
                "priority": "Medium",
                "is_against_authority": False
            }
            rephrased_text = original_text
            image_requirement = {"image_required": False}
        
        # Map category name to ID (if LLM returned name instead of ID)
        if "category" in categorization:
            category_query = select(ComplaintCategory.id).where(
                ComplaintCategory.name == categorization['category']
            )
            category_result = await self.db.execute(category_query)
            category_row = category_result.first()
            if category_row:
                category_id = category_row[0]

        # Calculate initial priority score
        priority = categorization.get("priority", "Medium")
        priority_score = PRIORITY_SCORES.get(priority, 50.0)

        # ✅ UPDATED: Spam is rejected before reaching this point, so status is always "Raised"
        initial_status = "Raised"

        # ✅ FIXED: Use timezone-aware datetime
        current_time = datetime.now(timezone.utc)
        
        # ✅ NEW: Process image if provided
        image_bytes = None
        image_mimetype = None
        image_size = None
        image_filename = None
        image_verified = False
        image_verification_status = "Pending"
        image_verification_message = None
        
        if image_file:
            try:
                # Read image bytes
                image_bytes, image_mimetype, image_size, image_filename = await file_upload_handler.read_image_bytes(
                    image_file, validate=True
                )
                
                # Optimize image
                image_bytes, image_size = await file_upload_handler.optimize_image_bytes(
                    image_bytes, image_mimetype
                )
                
                logger.info(f"Image uploaded: {image_filename} ({image_size} bytes)")
                
            except Exception as e:
                logger.error(f"Image upload error: {e}")
                # Continue without image
                image_bytes = None
        
        # ✅ UPDATED: Create complaint (spam is rejected, so no spam fields needed)
        complaint = await self.complaint_repo.create(
            student_roll_no=student_roll_no,
            category_id=category_id,
            original_text=original_text,
            rephrased_text=rephrased_text,
            visibility=visibility,
            priority=priority,
            priority_score=priority_score,
            status=initial_status,
            is_marked_as_spam=False,  # Spam complaints are rejected, never created
            spam_reason=None,
            complaint_department_id=student.department_id,
            # ✅ NEW: Binary image fields
            image_data=image_bytes,
            image_mimetype=image_mimetype,
            image_size=image_size,
            image_filename=image_filename,
            image_verified=False,
            image_verification_status="Pending" if image_bytes else None
        )
        
        # ✅ NEW: Verify image if provided
        if image_bytes:
            try:
                verification_result = await image_verification_service.verify_image_from_bytes(
                    db=self.db,
                    complaint_id=complaint.id,
                    complaint_text=rephrased_text,
                    image_bytes=image_bytes,
                    mimetype=image_mimetype
                )
                
                # Update complaint with verification results
                complaint.image_verified = verification_result["is_relevant"]
                complaint.image_verification_status = verification_result["status"]
                await self.db.commit()
                
                image_verified = verification_result["is_relevant"]
                image_verification_status = verification_result["status"]
                image_verification_message = verification_result["explanation"]
                
                logger.info(
                    f"Image verification for {complaint.id}: "
                    f"Verified={image_verified}, Status={image_verification_status}"
                )
                
            except Exception as e:
                logger.error(f"Image verification error: {e}")
                image_verification_message = f"Verification error: {str(e)}"
        
        # ✅ UPDATED: Route to appropriate authority (spam is already rejected)
        authority = None
        try:
            authority = await authority_service.route_complaint(
                self.db,
                category_id,
                student.department_id,
                categorization.get("is_against_authority", False)
            )

            if authority:
                complaint.assigned_authority_id = authority.id
                complaint.assigned_at = current_time
                await self.db.commit()

                # Create notification for authority
                await notification_service.create_notification(
                    self.db,
                    recipient_type="Authority",
                    recipient_id=str(authority.id),
                    complaint_id=complaint.id,
                    notification_type="complaint_assigned",
                    message=f"New complaint assigned: {rephrased_text[:100]}..."
                )

                logger.info(f"Complaint {complaint.id} assigned to {authority.name}")
            else:
                logger.warning(f"No authority found for complaint {complaint.id}")

        except Exception as e:
            logger.error(f"Authority routing error: {e}")
            # Continue without authority assignment

        logger.info(
            f"Complaint {complaint.id} created successfully - "
            f"Status: {initial_status}, Priority: {priority}, "
            f"Has Image: {image_bytes is not None}, "
            f"Image Required: {image_requirement.get('image_required', False)}"
        )

        return {
            "id": str(complaint.id),
            "status": "Submitted",
            "rephrased_text": rephrased_text,
            "original_text": original_text,
            "priority": priority,
            "priority_score": priority_score,
            "assigned_authority": authority.name if authority else None,
            "assigned_authority_id": authority.id if authority else None,
            "created_at": current_time.isoformat(),
            "message": "Complaint submitted successfully",
            # ✅ NEW: Image information
            "has_image": image_bytes is not None,
            "image_verified": image_verified,
            "image_verification_status": image_verification_status,
            "image_verification_message": image_verification_message,
            "image_filename": image_filename,
            "image_size": image_size,
            # ✅ NEW: Image requirement information
            "image_was_required": image_requirement.get("image_required", False),
            "image_requirement_reasoning": image_requirement.get("reasoning")
        }
    
    async def upload_complaint_image(
        self,
        complaint_id: UUID,
        student_roll_no: str,
        image_file: UploadFile
    ) -> Dict[str, Any]:
        """
        ✅ NEW: Upload/update image for existing complaint.
        
        Args:
            complaint_id: Complaint UUID
            student_roll_no: Student roll number (for permission check)
            image_file: Uploaded image file
        
        Returns:
            Image upload and verification results
        """
        # Get complaint and verify ownership
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        if complaint.student_roll_no != student_roll_no:
            raise PermissionError("Not authorized to upload image for this complaint")
        
        try:
            # Read and optimize image
            image_bytes, image_mimetype, image_size, image_filename = await file_upload_handler.read_image_bytes(
                image_file, validate=True
            )
            
            image_bytes, image_size = await file_upload_handler.optimize_image_bytes(
                image_bytes, image_mimetype
            )
            
            # Update complaint with image (has_image is a computed property based on image_data)
            complaint.image_data = image_bytes
            complaint.image_mimetype = image_mimetype
            complaint.image_size = image_size
            complaint.image_filename = image_filename
            complaint.image_verified = False
            complaint.image_verification_status = "Pending"
            await self.db.commit()
            
            # Verify image
            verification_result = await image_verification_service.verify_image_from_bytes(
                db=self.db,
                complaint_id=complaint.id,
                complaint_text=complaint.rephrased_text or complaint.original_text,
                image_bytes=image_bytes,
                mimetype=image_mimetype
            )
            
            # Update verification results
            complaint.image_verified = verification_result["is_relevant"]
            complaint.image_verification_status = verification_result["status"]
            await self.db.commit()
            
            logger.info(
                f"Image uploaded for complaint {complaint_id}: "
                f"Verified={verification_result['is_relevant']}, "
                f"Status={verification_result['status']}"
            )
            
            return {
                "complaint_id": str(complaint_id),
                "has_image": True,
                "image_verified": verification_result["is_relevant"],
                "verification_status": verification_result["status"],
                "verification_message": verification_result["explanation"],
                "image_filename": image_filename,
                "image_size": image_size,
                "confidence_score": verification_result.get("confidence_score", 0.0)
            }
            
        except Exception as e:
            logger.error(f"Image upload error for {complaint_id}: {e}")
            raise ValueError(f"Failed to upload image: {str(e)}")
    
    async def get_complaint_image(
        self,
        complaint_id: UUID,
        requester_roll_no: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        ✅ NEW: Get complaint image data.
        
        Args:
            complaint_id: Complaint UUID
            requester_roll_no: Optional student requesting image (for permission check)
        
        Returns:
            Dictionary with image_bytes, mimetype, and metadata
        """
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        # Check permission for private complaints
        if complaint.visibility == "Private":
            if not requester_roll_no or complaint.student_roll_no != requester_roll_no:
                raise PermissionError("Not authorized to view this complaint's image")
        
        if not complaint.has_image or not complaint.image_data:
            raise ValueError("Complaint has no image")
        
        return {
            "complaint_id": str(complaint_id),
            "image_bytes": complaint.image_data,
            "mimetype": complaint.image_mimetype,
            "filename": complaint.image_filename,
            "size": complaint.image_size,
            "verified": complaint.image_verified,
            "verification_status": complaint.image_verification_status
        }
    
    async def update_complaint_status(
        self,
        complaint_id: UUID,
        new_status: str,
        authority_id: int,
        reason: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Update complaint status (by authority).
        
        Args:
            complaint_id: Complaint UUID
            new_status: New status (Raised, In Progress, Resolved, Rejected, Escalated)
            authority_id: Authority making the change
            reason: Optional reason for change
        
        Returns:
            Updated complaint info
        """
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        # Check if authority has permission
        if complaint.assigned_authority_id != authority_id:
            raise PermissionError("Not authorized to update this complaint")
        
        old_status = complaint.status
        
        # Don't allow updating already resolved complaints
        if old_status == "Resolved" and new_status != "Reopened":
            raise ValueError("Cannot modify resolved complaint")
        
        # Update status
        complaint.status = new_status
        
        # ✅ FIXED: Use timezone-aware datetime
        current_time = datetime.now(timezone.utc)
        
        # Update resolved_at if status is Resolved
        if new_status == "Resolved":
            complaint.resolved_at = current_time
        elif new_status == "Reopened":
            complaint.resolved_at = None
        
        await self.db.commit()
        
        # Create status update record
        status_update = StatusUpdate(
            complaint_id=complaint_id,
            old_status=old_status,
            new_status=new_status,
            updated_by=authority_id,
            reason=reason,
            updated_at=current_time
        )
        self.db.add(status_update)
        await self.db.commit()
        
        # Notify student
        await notification_service.create_notification(
            self.db,
            recipient_type="Student",
            recipient_id=complaint.student_roll_no,
            complaint_id=complaint_id,
            notification_type="status_update",
            message=f"Your complaint status changed to '{new_status}'" + 
                    (f": {reason}" if reason else "")
        )
        
        logger.info(
            f"Complaint {complaint_id} status updated by authority {authority_id}: "
            f"{old_status} → {new_status}"
        )
        
        return {
            "complaint_id": str(complaint_id),
            "old_status": old_status,
            "new_status": new_status,
            "updated_at": current_time.isoformat(),
            "reason": reason,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None
        }
    
    async def get_public_feed(
        self,
        student_roll_no: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get public feed filtered by visibility rules.
        
        Args:
            student_roll_no: Student requesting feed
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of complaint dictionaries
        """
        student = await self.student_repo.get_with_department(student_roll_no)
        if not student:
            raise ValueError("Student not found")
        
        complaints = await self.complaint_repo.get_public_feed(
            student_stay_type=student.stay_type,
            student_department_id=student.department_id,
            skip=skip,
            limit=limit
        )
        
        # Format complaints for response
        result = []
        for complaint in complaints:
            result.append({
                "id": str(complaint.id),
                "rephrased_text": complaint.rephrased_text,
                "category": complaint.category.name if complaint.category else "Unknown",
                "priority": complaint.priority,
                "status": complaint.status,
                "upvotes": complaint.upvotes,
                "downvotes": complaint.downvotes,
                "created_at": complaint.submitted_at.isoformat(),
                "visibility": complaint.visibility,
                "is_own_complaint": complaint.student_roll_no == student_roll_no,
                # ✅ NEW: Image fields
                "has_image": complaint.has_image,
                "image_verified": complaint.image_verified,
                "image_verification_status": complaint.image_verification_status
            })
        
        return result
    
    async def get_complaint_details(
        self,
        complaint_id: UUID,
        requester_roll_no: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get detailed complaint information.
        
        Args:
            complaint_id: Complaint UUID
            requester_roll_no: Optional student requesting details
        
        Returns:
            Detailed complaint info
        """
        complaint = await self.complaint_repo.get_with_relations(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        # Check if requester has permission to view
        if complaint.visibility == "Private":
            if not requester_roll_no or complaint.student_roll_no != requester_roll_no:
                raise PermissionError("Not authorized to view this complaint")
        
        return {
            "id": str(complaint.id),
            "original_text": complaint.original_text,
            "rephrased_text": complaint.rephrased_text,
            "category": complaint.category.name if complaint.category else "Unknown",
            "priority": complaint.priority,
            "priority_score": complaint.priority_score,
            "status": complaint.status,
            "visibility": complaint.visibility,
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "created_at": complaint.submitted_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "assigned_authority": complaint.assigned_authority.name if complaint.assigned_authority else None,
            "student_roll_no": complaint.student_roll_no if complaint.visibility != "Anonymous" else "Anonymous",
            "is_spam": complaint.is_marked_as_spam,
            # ✅ NEW: Image fields (no image_url)
            "has_image": complaint.has_image,
            "image_verified": complaint.image_verified,
            "image_verification_status": complaint.image_verification_status,
            "image_filename": complaint.image_filename,
            "image_size": complaint.image_size
        }
    
    async def get_student_complaints(
        self,
        student_roll_no: str,
        skip: int = 0,
        limit: int = 20
    ) -> List[Dict[str, Any]]:
        """
        Get all complaints by a student with status tracking.
        
        Args:
            student_roll_no: Student roll number
            skip: Number to skip
            limit: Maximum results
        
        Returns:
            List of student's complaints with status info
        """
        complaints = await self.complaint_repo.get_by_student(
            student_roll_no, skip=skip, limit=limit
        )
        
        result = []
        for complaint in complaints:
            result.append({
                "id": str(complaint.id),
                "title": complaint.rephrased_text[:100] + "..." if len(complaint.rephrased_text) > 100 else complaint.rephrased_text,
                "category": complaint.category.name if complaint.category else "Unknown",
                "status": complaint.status,
                "priority": complaint.priority,
                "created_at": complaint.submitted_at.isoformat(),
                "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
                "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
                "assigned_authority": complaint.assigned_authority.name if complaint.assigned_authority else "Unassigned",
                "upvotes": complaint.upvotes,
                "downvotes": complaint.downvotes,
                "visibility": complaint.visibility,
                # ✅ NEW: Image fields
                "has_image": complaint.has_image,
                "image_verified": complaint.image_verified
            })
        
        return result
    
    async def get_complaint_status_history(
        self,
        complaint_id: UUID,
        student_roll_no: str
    ) -> List[Dict[str, Any]]:
        """
        Get status update history for a complaint.
        
        Args:
            complaint_id: Complaint UUID
            student_roll_no: Student requesting history (for permission check)
        
        Returns:
            List of status updates
        """
        # Verify ownership
        complaint = await self.complaint_repo.get(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")
        
        if complaint.student_roll_no != student_roll_no:
            raise PermissionError("Not authorized to view this complaint history")
        
        # Get status history
        query = select(StatusUpdate).where(
            StatusUpdate.complaint_id == complaint_id
        ).order_by(StatusUpdate.updated_at.asc())
        
        result = await self.db.execute(query)
        status_updates = result.scalars().all()
        
        history = []
        for update in status_updates:
            history.append({
                "old_status": update.old_status,
                "new_status": update.new_status,
                "updated_at": update.updated_at.isoformat() if update.updated_at else datetime.now(timezone.utc).isoformat(),
                "reason": update.reason,
                "updated_by_authority_id": update.updated_by
            })
        
        return history
    
    async def get_complaint_statistics(
        self,
        student_roll_no: str
    ) -> Dict[str, Any]:
        """
        Get complaint statistics for a student.

        Args:
            student_roll_no: Student roll number

        Returns:
            Statistics dictionary
        """
        complaints = await self.complaint_repo.get_by_student(student_roll_no)

        total = len(complaints)
        resolved = sum(1 for c in complaints if c.status == "Resolved")
        in_progress = sum(1 for c in complaints if c.status == "In Progress")
        raised = sum(1 for c in complaints if c.status == "Raised")
        spam = sum(1 for c in complaints if c.is_marked_as_spam)
        with_images = sum(1 for c in complaints if c.has_image)  # ✅ NEW
        verified_images = sum(1 for c in complaints if c.image_verified)  # ✅ NEW

        return {
            "total_complaints": total,
            "resolved": resolved,
            "in_progress": in_progress,
            "raised": raised,
            "spam_flagged": spam,
            "resolution_rate": (resolved / total * 100) if total > 0 else 0,
            # ✅ NEW: Image statistics
            "with_images": with_images,
            "verified_images": verified_images
        }

    # ==================== PARTIAL ANONYMITY ====================

    async def get_complaint_for_authority(
        self,
        complaint_id: UUID,
        authority_id: int,
        is_admin: bool = False
    ) -> Dict[str, Any]:
        """
        ✅ NEW: Get complaint with partial anonymity enforcement.

        Rules:
        - Admin: Can view all student information for all complaints
        - Authority: Can view student info ONLY if complaint is marked as spam
        - Non-spam complaints: Hide student personal details from authorities

        Args:
            complaint_id: Complaint UUID
            authority_id: Authority requesting details
            is_admin: Whether requester is admin

        Returns:
            Complaint with conditionally redacted student info
        """
        complaint = await self.complaint_repo.get_with_relations(complaint_id)
        if not complaint:
            raise ValueError("Complaint not found")

        # Check if authority has permission to view
        if not is_admin and complaint.assigned_authority_id != authority_id:
            raise PermissionError("Not authorized to view this complaint")

        # Build base response
        response = {
            "id": str(complaint.id),
            "original_text": complaint.original_text,
            "rephrased_text": complaint.rephrased_text,
            "category": complaint.category.name if complaint.category else "Unknown",
            "priority": complaint.priority,
            "priority_score": complaint.priority_score,
            "status": complaint.status,
            "visibility": complaint.visibility,
            "upvotes": complaint.upvotes,
            "downvotes": complaint.downvotes,
            "created_at": complaint.submitted_at.isoformat(),
            "updated_at": complaint.updated_at.isoformat() if complaint.updated_at else None,
            "resolved_at": complaint.resolved_at.isoformat() if complaint.resolved_at else None,
            "assigned_authority": complaint.assigned_authority.name if complaint.assigned_authority else None,
            "is_spam": complaint.is_marked_as_spam,
            "spam_reason": complaint.spam_reason,
            # Image fields
            "has_image": complaint.has_image,
            "image_verified": complaint.image_verified,
            "image_verification_status": complaint.image_verification_status,
            "image_filename": complaint.image_filename,
            "image_size": complaint.image_size
        }

        # ✅ CRITICAL: Partial Anonymity Logic
        if is_admin:
            # Admin can see ALL student information
            response["student_roll_no"] = complaint.student_roll_no
            response["student_name"] = complaint.student.name if complaint.student else None
            response["student_email"] = complaint.student.email if complaint.student else None
            response["student_gender"] = complaint.student.gender if complaint.student else None
            response["student_stay_type"] = complaint.student.stay_type if complaint.student else None
            response["student_year"] = complaint.student.year if complaint.student else None
            response["student_department"] = complaint.student.department.name if complaint.student and complaint.student.department else None
            logger.info(f"Admin {authority_id} viewing complaint {complaint_id} - Full student info provided")

        elif complaint.is_marked_as_spam:
            # Authority can see student info for SPAM complaints
            response["student_roll_no"] = complaint.student_roll_no
            response["student_name"] = complaint.student.name if complaint.student else None
            response["student_email"] = complaint.student.email if complaint.student else None
            response["student_gender"] = complaint.student.gender if complaint.student else None
            response["student_stay_type"] = complaint.student.stay_type if complaint.student else None
            response["student_year"] = complaint.student.year if complaint.student else None
            response["student_department"] = complaint.student.department.name if complaint.student and complaint.student.department else None
            logger.info(
                f"Authority {authority_id} viewing SPAM complaint {complaint_id} - "
                f"Student info revealed: {complaint.student_roll_no}"
            )

        else:
            # Non-spam complaints: Hide student details from authorities
            response["student_roll_no"] = "Hidden (non-spam)"
            response["student_name"] = "Hidden (non-spam)"
            response["student_email"] = "Hidden (non-spam)"
            response["student_gender"] = None
            response["student_stay_type"] = None
            response["student_year"] = None
            response["student_department"] = None
            logger.info(
                f"Authority {authority_id} viewing NON-SPAM complaint {complaint_id} - "
                f"Student info hidden (partial anonymity)"
            )

        return response


__all__ = ["ComplaintService"]
