"""
File upload and storage utilities.

✅ FIXED: Added binary image reading methods for database storage
✅ FIXED: Added base64 data URI conversion for Groq Vision API
✅ FIXED: Added thumbnail generation
✅ FIXED: Logging conflict with 'filename' reserved attribute
✅ FIXED: Unicode arrow replaced with ASCII for Windows console
✅ KEPT: Filesystem methods for backward compatibility
"""

import os
import uuid
import shutil
import base64
from io import BytesIO
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from fastapi import UploadFile
from PIL import Image
from src.config.settings import settings
from src.utils.exceptions import InvalidFileTypeError, FileTooLargeError, FileUploadError
from src.utils.validators import validate_file_extension
from src.utils.logger import app_logger


class FileUploadHandler:
    """Handler for file uploads (filesystem + binary database storage)"""
    
    def __init__(self):
        """Initialize file upload handler"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_IMAGE_EXTENSIONS
        
        # Thumbnail settings
        self.thumbnail_size = (200, 200)  # Max dimensions for thumbnail
        self.thumbnail_quality = 70
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    # ==================== BINARY DATABASE STORAGE METHODS (NEW) ====================
    
    async def read_image_bytes(
        self,
        file: UploadFile,
        validate: bool = True
    ) -> Tuple[bytes, str, int, str]:
        """
        Read uploaded image as bytes for database storage.
        
        Args:
            file: Uploaded file
            validate: Whether to validate file
        
        Returns:
            Tuple of (image_bytes, mimetype, size, original_filename)
        
        Raises:
            InvalidFileTypeError: If file type is not allowed
            FileTooLargeError: If file size exceeds limit
        """
        if validate:
            # Validate file extension
            is_valid, error_msg = validate_file_extension(
                file.filename,
                self.allowed_extensions
            )
            if not is_valid:
                raise InvalidFileTypeError(self.allowed_extensions)
        
        # Read bytes
        image_bytes = await file.read()
        file_size = len(image_bytes)
        
        # Validate size
        if file_size > self.max_file_size:
            raise FileTooLargeError(self.max_file_size)
        
        # Get MIME type
        mimetype = file.content_type or self._guess_mimetype(file.filename)
        
        # ✅ FIXED: Use 'uploaded_filename' instead of 'filename' to avoid logging conflict
        app_logger.info(
            f"Read image bytes: {file.filename}",
            extra={
                "uploaded_filename": file.filename,
                "size_bytes": file_size,
                "mimetype": mimetype
            }
        )
        
        return image_bytes, mimetype, file_size, file.filename
    
    async def optimize_image_bytes(
        self,
        image_bytes: bytes,
        mimetype: str,
        max_width: int = 1920,
        max_height: int = 1920,
        quality: int = 85
    ) -> Tuple[bytes, int]:
        """
        Optimize image bytes (compress, resize) for database storage.
        
        Args:
            image_bytes: Original image bytes
            mimetype: MIME type (e.g., "image/jpeg")
            max_width: Maximum width
            max_height: Maximum height
            quality: JPEG quality (1-100)
        
        Returns:
            Tuple of (optimized_bytes, new_size)
        """
        try:
            # Open image from bytes
            img = Image.open(BytesIO(image_bytes))
            
            # Convert RGBA to RGB (for JPEG compatibility)
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            # Resize if too large
            if img.width > max_width or img.height > max_height:
                img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                app_logger.info(
                    f"Resized image from {img.size} to fit {max_width}x{max_height}"
                )
            
            # Save optimized to bytes
            output = BytesIO()
            img_format = "JPEG"  # Always save as JPEG for consistency
            img.save(output, format=img_format, optimize=True, quality=quality)
            optimized_bytes = output.getvalue()
            
            compression_ratio = (1 - len(optimized_bytes) / len(image_bytes)) * 100
            
            # ✅ FIXED: Replace Unicode arrow → with ASCII ->
            app_logger.info(
                f"Optimized image: {len(image_bytes)} -> {len(optimized_bytes)} bytes "
                f"({compression_ratio:.1f}% reduction)"
            )
            
            return optimized_bytes, len(optimized_bytes)
        
        except Exception as e:
            app_logger.warning(f"Image optimization failed: {e}, using original")
            return image_bytes, len(image_bytes)
    
    async def create_thumbnail(
        self,
        image_bytes: bytes,
        size: Optional[Tuple[int, int]] = None
    ) -> Tuple[bytes, int]:
        """
        Create thumbnail from image bytes.
        
        Args:
            image_bytes: Original image bytes
            size: Thumbnail size (width, height), defaults to self.thumbnail_size
        
        Returns:
            Tuple of (thumbnail_bytes, size)
        """
        try:
            size = size or self.thumbnail_size
            
            # Open image
            img = Image.open(BytesIO(image_bytes))
            
            # Convert to RGB
            if img.mode == "RGBA":
                rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[3])
                img = rgb_img
            elif img.mode not in ("RGB", "L"):
                img = img.convert("RGB")
            
            # Create thumbnail (maintains aspect ratio)
            img.thumbnail(size, Image.Resampling.LANCZOS)
            
            # Save to bytes
            output = BytesIO()
            img.save(output, format="JPEG", optimize=True, quality=self.thumbnail_quality)
            thumbnail_bytes = output.getvalue()
            
            app_logger.info(
                f"Created thumbnail: {img.size} ({len(thumbnail_bytes)} bytes)"
            )
            
            return thumbnail_bytes, len(thumbnail_bytes)
        
        except Exception as e:
            app_logger.error(f"Thumbnail creation failed: {e}")
            raise FileUploadError(f"Failed to create thumbnail: {str(e)}")
    
    def bytes_to_data_uri(
        self,
        image_bytes: bytes,
        mimetype: str
    ) -> str:
        """
        Convert image bytes to base64 data URI for Groq Vision API.
        
        Args:
            image_bytes: Image bytes
            mimetype: MIME type (e.g., "image/jpeg")
        
        Returns:
            Data URI string (data:image/jpeg;base64,...)
        """
        base64_image = base64.b64encode(image_bytes).decode('utf-8')
        return f"data:{mimetype};base64,{base64_image}"
    
    def data_uri_to_bytes(
        self,
        data_uri: str
    ) -> Tuple[bytes, str]:
        """
        Convert data URI back to bytes.
        
        Args:
            data_uri: Data URI string
        
        Returns:
            Tuple of (image_bytes, mimetype)
        """
        try:
            # Parse data URI: data:image/jpeg;base64,ABC123...
            header, encoded = data_uri.split(",", 1)
            mimetype = header.split(";")[0].split(":")[1]
            image_bytes = base64.b64decode(encoded)
            return image_bytes, mimetype
        except Exception as e:
            raise FileUploadError(f"Invalid data URI: {str(e)}")
    
    def get_image_metadata(
        self,
        image_bytes: bytes
    ) -> dict:
        """
        Get image metadata from bytes.
        
        Args:
            image_bytes: Image bytes
        
        Returns:
            Dictionary with metadata
        """
        try:
            with Image.open(BytesIO(image_bytes)) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": len(image_bytes)
                }
        except Exception as e:
            app_logger.warning(f"Failed to get image metadata: {e}")
            return {"size_bytes": len(image_bytes)}
    
    # ==================== FILESYSTEM STORAGE METHODS (LEGACY - KEPT FOR COMPATIBILITY) ====================
    
    async def save_image(
        self,
        file: UploadFile,
        subfolder: Optional[str] = None
    ) -> Tuple[str, dict]:
        """
        Save uploaded image file to filesystem.
        
        ⚠️ LEGACY METHOD: Use read_image_bytes() for database storage instead
        
        Args:
            file: Uploaded file
            subfolder: Optional subfolder name
        
        Returns:
            Tuple of (file_path, metadata)
        
        Raises:
            InvalidFileTypeError: If file type is not allowed
            FileTooLargeError: If file size exceeds limit
            FileUploadError: If upload fails
        """
        # Validate file extension
        is_valid, error_msg = validate_file_extension(
            file.filename,
            self.allowed_extensions
        )
        if not is_valid:
            raise InvalidFileTypeError(self.allowed_extensions)
        
        # Check file size
        file.file.seek(0, 2)  # Seek to end
        file_size = file.file.tell()
        file.file.seek(0)  # Reset to start
        
        if file_size > self.max_file_size:
            raise FileTooLargeError(self.max_file_size)
        
        # Generate unique filename
        ext = file.filename.rsplit(".", 1)[1].lower()
        unique_filename = f"{uuid.uuid4()}.{ext}"
        
        # Determine save path
        if subfolder:
            save_dir = self.upload_dir / subfolder
            save_dir.mkdir(parents=True, exist_ok=True)
        else:
            save_dir = self.upload_dir
        
        file_path = save_dir / unique_filename
        
        try:
            # Save file
            with open(file_path, "wb") as buffer:
                shutil.copyfileobj(file.file, buffer)
            
            # Get image metadata
            metadata = self._get_image_metadata_from_path(file_path)
            
            # Optimize image if needed
            await self._optimize_image(file_path)
            
            # Return relative path for storage
            relative_path = str(file_path.relative_to(self.upload_dir.parent))
            
            return relative_path, metadata
            
        except Exception as e:
            # Cleanup on error
            if file_path.exists():
                file_path.unlink()
            raise FileUploadError(f"Failed to save file: {str(e)}")
    
    def _get_image_metadata_from_path(self, file_path: Path) -> dict:
        """
        Get image metadata from file path.
        
        Args:
            file_path: Path to image file
        
        Returns:
            Dictionary with metadata
        """
        try:
            with Image.open(file_path) as img:
                return {
                    "width": img.width,
                    "height": img.height,
                    "format": img.format,
                    "mode": img.mode,
                    "size_bytes": file_path.stat().st_size
                }
        except Exception:
            return {}
    
    async def _optimize_image(self, file_path: Path):
        """
        Optimize image on filesystem (resize if too large, compress).
        
        Args:
            file_path: Path to image file
        """
        try:
            with Image.open(file_path) as img:
                # Convert RGBA to RGB if needed
                if img.mode == "RGBA":
                    rgb_img = Image.new("RGB", img.size, (255, 255, 255))
                    rgb_img.paste(img, mask=img.split()[3])
                    img = rgb_img
                
                # Resize if too large
                max_width = 1920
                max_height = 1920
                
                if img.width > max_width or img.height > max_height:
                    img.thumbnail((max_width, max_height), Image.Resampling.LANCZOS)
                
                # Save with optimization
                img.save(
                    file_path,
                    optimize=True,
                    quality=85
                )
        except Exception as e:
            # If optimization fails, keep original but log the issue
            app_logger.warning(
                f"Image optimization failed for {file_path.name}",
                extra={
                    "file_path": str(file_path),
                    "error_type": type(e).__name__,
                    "error_message": str(e)
                }
            )
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete uploaded file from filesystem.
        
        Args:
            file_path: File path (relative or absolute)
        
        Returns:
            True if deleted, False otherwise
        """
        try:
            path = Path(file_path)
            if not path.is_absolute():
                path = self.upload_dir.parent / file_path
            
            if path.exists():
                path.unlink()
                return True
        except Exception:
            pass
        return False
    
    def get_file_url(self, file_path: str, base_url: str = "") -> str:
        """
        Get URL for uploaded file.
        
        Args:
            file_path: File path (relative)
            base_url: Base URL for the application
        
        Returns:
            Full URL to file
        """
        return f"{base_url}/{file_path}".replace("\\", "/")
    
    # ==================== UTILITY METHODS ====================
    
    def _guess_mimetype(self, filename: str) -> str:
        """
        Guess MIME type from filename.
        
        Args:
            filename: File name
        
        Returns:
            MIME type string
        """
        ext = filename.rsplit(".", 1)[-1].lower()
        mime_types = {
            "jpg": "image/jpeg",
            "jpeg": "image/jpeg",
            "png": "image/png",
            "gif": "image/gif",
            "webp": "image/webp",
            "bmp": "image/bmp"
        }
        return mime_types.get(ext, "image/jpeg")


# Global file upload handler
file_upload_handler = FileUploadHandler()


__all__ = ["FileUploadHandler", "file_upload_handler"]
