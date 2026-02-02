"""
Authentication service for JWT tokens and password hashing.
"""

import logging
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
from jose import JWTError, jwt
from passlib.context import CryptContext
from src.config.settings import settings

logger = logging.getLogger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class AuthService:
    """Service for authentication operations"""
    
    @staticmethod
    def hash_password(password: str) -> str:
        """
        Hash a password using bcrypt.
        
        Args:
            password: Plain text password
        
        Returns:
            Hashed password
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """
        Verify a password against its hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password from database
        
        Returns:
            True if password matches
        """
        try:
            return pwd_context.verify(plain_password, hashed_password)
        except Exception as e:
            logger.error(f"Password verification error: {e}")
            return False
    
    @staticmethod
    def create_access_token(
        subject: str,
        role: str,
        additional_claims: Optional[Dict[str, Any]] = None,
        expires_delta: Optional[timedelta] = None
    ) -> str:
        """
        Create JWT access token.
        
        Args:
            subject: Token subject (roll_no or authority_id)
            role: User role (Student, Authority, Admin)
            additional_claims: Additional JWT claims
            expires_delta: Token expiration duration
        
        Returns:
            Encoded JWT token
        """
        if expires_delta is None:
            expires_delta = timedelta(days=settings.JWT_EXPIRATION_DAYS)
        
        expire = datetime.utcnow() + expires_delta
        
        to_encode = {
            "sub": subject,
            "role": role,
            "exp": expire,
            "iat": datetime.utcnow(),
        }
        
        # Add additional claims
        if additional_claims:
            to_encode.update(additional_claims)
        
        try:
            encoded_jwt = jwt.encode(
                to_encode,
                settings.JWT_SECRET_KEY,
                algorithm=settings.JWT_ALGORITHM
            )
            logger.info(f"Token created for {subject} ({role})")
            return encoded_jwt
        except Exception as e:
            logger.error(f"Token creation error: {e}")
            raise
    
    @staticmethod
    def decode_token(token: str) -> Optional[Dict[str, Any]]:
        """
        Decode and verify JWT token.
        
        Args:
            token: JWT token string
        
        Returns:
            Decoded token payload or None if invalid
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            return payload
        except JWTError as e:
            logger.warning(f"Token decode error: {e}")
            return None
    
    @staticmethod
    def get_token_expiration_seconds() -> int:
        """
        Get token expiration duration in seconds.
        
        Returns:
            Expiration duration in seconds
        """
        return settings.JWT_EXPIRATION_DAYS * 24 * 60 * 60
    
    @staticmethod
    def validate_password_strength(password: str) -> tuple[bool, Optional[str]]:
        """
        Validate password strength.
        
        Args:
            password: Password to validate
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if len(password) < settings.PASSWORD_MIN_LENGTH:
            return False, f"Password must be at least {settings.PASSWORD_MIN_LENGTH} characters"
        
        if not any(char.isdigit() for char in password):
            return False, "Password must contain at least one digit"
        
        if not any(char.isupper() for char in password):
            return False, "Password must contain at least one uppercase letter"
        
        if not any(char.islower() for char in password):
            return False, "Password must contain at least one lowercase letter"
        
        # Optional: Check for special characters
        # special_chars = "!@#$%^&*()_+-=[]{}|;:,.<>?"
        # if not any(char in special_chars for char in password):
        #     return False, "Password must contain at least one special character"
        
        return True, None


# Create global instance
auth_service = AuthService()

__all__ = ["AuthService", "auth_service"]
