"""
File upload and storage utilities.
"""

import os
import uuid
import shutil
from pathlib import Path
from typing import Optional, Tuple
from datetime import datetime
from fastapi import UploadFile
from PIL import Image
from src.config.settings import settings
from src.utils.exceptions import InvalidFileTypeError, FileTooLargeError, FileUploadError
from src.utils.validators import validate_file_extension


class FileUploadHandler:
    """Handler for file uploads"""
    
    def __init__(self):
        """Initialize file upload handler"""
        self.upload_dir = Path(settings.UPLOAD_DIR)
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_extensions = settings.ALLOWED_IMAGE_EXTENSIONS
        
        # Create upload directory if it doesn't exist
        self.upload_dir.mkdir(parents=True, exist_ok=True)
    
    async def save_image(
        self,
        file: UploadFile,
        subfolder: Optional[str] = None
    ) -> Tuple[str, dict]:
        """
        Save uploaded image file.
        
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
            metadata = self._get_image_metadata(file_path)
            
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
    
    def _get_image_metadata(self, file_path: Path) -> dict:
        """
        Get image metadata.
        
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
        Optimize image (resize if too large, compress).
        
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
            # If optimization fails, keep original
            pass
    
    def delete_file(self, file_path: str) -> bool:
        """
        Delete uploaded file.
        
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


# Global file upload handler
file_upload_handler = FileUploadHandler()


__all__ = ["FileUploadHandler", "file_upload_handler"]
