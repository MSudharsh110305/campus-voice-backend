"""
Application settings using Pydantic Settings.
Loads configuration from environment variables with full validation.
"""

from typing import List, Optional, Dict
from pydantic import Field, field_validator, computed_field
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    """
    Application settings loaded from environment variables.
    Uses .env file for local development.
    """
    
    # ==================== APPLICATION ====================
    ENVIRONMENT: str = Field(
        default="development",
        description="Application environment: development, staging, production"
    )
    DEBUG: bool = Field(
        default=False,
        description="Enable debug mode"
    )
    APP_NAME: str = Field(
        default="CampusVoice",
        description="Application name"
    )
    HOST: str = Field(
        default="0.0.0.0",
        description="Server host address"
    )
    PORT: int = Field(
        default=8000,
        ge=1000,
        le=65535,
        description="Server port"
    )
    WORKERS: int = Field(
        default=4,
        ge=1,
        description="Number of worker processes"
    )
    
    # ==================== DATABASE ====================
    DATABASE_URL: str = Field(
        ...,
        description="PostgreSQL connection string (asyncpg format)"
    )
    DB_ECHO: bool = Field(
        default=False,
        description="Echo SQL queries to console"
    )
    DB_POOL_SIZE: int = Field(
        default=20,
        ge=1,
        description="Database connection pool size"
    )
    DB_MAX_OVERFLOW: int = Field(
        default=10,
        ge=0,
        description="Maximum overflow connections"
    )
    DB_POOL_TIMEOUT: int = Field(
        default=30,
        ge=1,
        description="Pool timeout in seconds"
    )
    DB_POOL_RECYCLE: int = Field(
        default=3600,
        ge=300,
        description="Pool recycle time in seconds"
    )
    
    # ==================== JWT & SECURITY ====================
    JWT_SECRET_KEY: str = Field(
        ...,
        min_length=32,
        description="Secret key for JWT token signing (min 32 chars)"
    )
    JWT_ALGORITHM: str = Field(
        default="HS256",
        description="JWT signing algorithm"
    )
    JWT_EXPIRATION_DAYS: int = Field(
        default=7,
        ge=1,
        description="JWT token expiration in days"
    )
    PASSWORD_MIN_LENGTH: int = Field(
        default=8,
        ge=6,
        description="Minimum password length"
    )
    
    # ==================== GROQ LLM ====================
    GROQ_API_KEY: str = Field(
        ...,
        description="Groq API key for LLM operations"
    )
    LLM_MODEL: str = Field(
        default="llama-3.1-8b-instant",
        description="Primary LLM model to use"
    )
    LLM_TEMPERATURE: float = Field(
        default=0.3,
        ge=0.0,
        le=2.0,
        description="LLM temperature for generation"
    )
    LLM_MAX_TOKENS: int = Field(
        default=500,
        ge=50,
        le=4000,
        description="Maximum tokens per LLM response"
    )
    LLM_TIMEOUT: int = Field(
        default=30,
        ge=5,
        description="LLM request timeout in seconds"
    )
    LLM_MAX_RETRIES: int = Field(
        default=3,
        ge=1,
        le=10,
        description="Maximum retry attempts for LLM requests"
    )
    
    # ==================== CORS ====================
    CORS_ORIGINS: List[str] = Field(
        default=["http://localhost:3000"],
        description="Allowed CORS origins"
    )
    CORS_ALLOW_CREDENTIALS: bool = Field(
        default=True,
        description="Allow credentials in CORS"
    )
    CORS_ALLOW_METHODS: List[str] = Field(
        default=["GET", "POST", "PUT", "DELETE", "PATCH", "OPTIONS"],
        description="Allowed HTTP methods"
    )
    CORS_ALLOW_HEADERS: List[str] = Field(
        default=["*"],
        description="Allowed HTTP headers"
    )
    
    # ==================== RATE LIMITING ====================
    RATE_LIMIT_ENABLED: bool = Field(
        default=True,
        description="Enable rate limiting"
    )
    RATE_LIMIT_STUDENT_COMPLAINTS_PER_DAY: int = Field(
        default=5,
        ge=1,
        description="Max complaints per student per day"
    )
    RATE_LIMIT_STUDENT_API_PER_HOUR: int = Field(
        default=100,
        ge=10,
        description="Max API calls per student per hour"
    )
    RATE_LIMIT_AUTHORITY_API_PER_HOUR: int = Field(
        default=500,
        ge=100,
        description="Max API calls per authority per hour"
    )
    RATE_LIMIT_GLOBAL_PER_MINUTE: int = Field(
        default=60,
        ge=10,
        description="Global rate limit per minute"
    )
    
    # ==================== VOTING SYSTEM ====================
    MAX_VOTES_PER_COMPLAINT: int = Field(
        default=100,
        ge=10,
        description="Maximum votes allowed per complaint"
    )
    VOTE_IMPACT_MULTIPLIER: float = Field(
        default=2.0,
        ge=0.1,
        le=10.0,
        description="Multiplier for vote impact on priority"
    )
    UPVOTE_POINTS: int = Field(
        default=5,
        ge=1,
        description="Points awarded for upvote"
    )
    DOWNVOTE_POINTS: int = Field(
        default=-3,
        le=-1,
        description="Points deducted for downvote"
    )
    
    # ==================== PRIORITY CALCULATION ====================
    PRIORITY_LOW_MIN: int = Field(
        default=0,
        description="Minimum score for Low priority"
    )
    PRIORITY_MEDIUM_MIN: int = Field(
        default=50,
        ge=1,
        description="Minimum score for Medium priority"
    )
    PRIORITY_HIGH_MIN: int = Field(
        default=100,
        ge=50,
        description="Minimum score for High priority"
    )
    PRIORITY_CRITICAL_MIN: int = Field(
        default=200,
        ge=100,
        description="Minimum score for Critical priority"
    )
    
    # ==================== FILE UPLOAD ====================
    UPLOAD_DIR: str = Field(
        default="./uploads",
        description="Directory for uploaded files"
    )
    MAX_FILE_SIZE: int = Field(
        default=5242880,  # 5MB
        ge=1024,
        description="Maximum file size in bytes"
    )
    ALLOWED_IMAGE_EXTENSIONS: List[str] = Field(
        default=["jpg", "jpeg", "png", "gif", "webp"],
        description="Allowed image file extensions"
    )
    
    # ==================== LOGGING ====================
    LOG_LEVEL: str = Field(
        default="INFO",
        description="Logging level"
    )
    LOG_FORMAT: str = Field(
        default="text",
        description="Log format: json or text"
    )
    LOG_FILE: str = Field(
        default="./logs/campusvoice.log",
        description="Log file path"
    )
    
    # ==================== WEBSOCKET ====================
    WEBSOCKET_PING_INTERVAL: int = Field(
        default=30,
        ge=10,
        description="WebSocket ping interval in seconds"
    )
    WEBSOCKET_PING_TIMEOUT: int = Field(
        default=10,
        ge=5,
        description="WebSocket ping timeout in seconds"
    )
    MAX_WEBSOCKET_CONNECTIONS: int = Field(
        default=100,
        ge=10,
        description="Maximum WebSocket connections per user"
    )
    
    # ==================== DATA RETENTION ====================
    DATA_RETENTION_MONTHS: int = Field(
        default=6,
        ge=1,
        description="Data retention period in months"
    )
    AUTO_DELETE_OLD_COMPLAINTS: bool = Field(
        default=False,
        description="Automatically delete old complaints"
    )
    
    # ==================== FEATURE FLAGS ====================
    ENABLE_EMAIL_VERIFICATION: bool = Field(
        default=False,
        description="Enable email verification"
    )
    ENABLE_IMAGE_VERIFICATION: bool = Field(
        default=True,
        description="Enable image verification"
    )
    ENABLE_SPAM_DETECTION: bool = Field(
        default=True,
        description="Enable spam detection"
    )
    ENABLE_AUTO_ESCALATION: bool = Field(
        default=True,
        description="Enable automatic escalation"
    )
    ENABLE_WEBSOCKET: bool = Field(
        default=False,
        description="Enable WebSocket support"
    )
    
    # ==================== EMAIL SETTINGS ====================
    SMTP_HOST: str = Field(
        default="smtp.gmail.com",
        description="SMTP server host"
    )
    SMTP_PORT: int = Field(
        default=587,
        ge=1,
        le=65535,
        description="SMTP server port"
    )
    SMTP_USER: Optional[str] = Field(
        default=None,
        description="SMTP username"
    )
    SMTP_PASSWORD: Optional[str] = Field(
        default=None,
        description="SMTP password"
    )
    SMTP_FROM_EMAIL: str = Field(
        default="noreply@campusvoice.edu",
        description="Email sender address"
    )
    SMTP_FROM_NAME: str = Field(
        default="CampusVoice",
        description="Email sender name"
    )
    
    # ==================== FRONTEND ====================
    FRONTEND_URL: str = Field(
        default="http://localhost:3000",
        description="Frontend application URL"
    )
    
    # ==================== ADMIN SETTINGS ====================
    ADMIN_EMAIL: str = Field(
        default="admin@campusvoice.edu",
        description="Initial admin email"
    )
    ADMIN_PASSWORD: str = Field(
        default="Admin@123",
        min_length=8,
        description="Initial admin password"
    )
    ADMIN_NAME: str = Field(
        default="System Administrator",
        description="Initial admin name"
    )
    
    # ==================== COMPLAINT SETTINGS ====================
    MIN_COMPLAINT_LENGTH: int = Field(
        default=10,
        ge=5,
        description="Minimum complaint text length"
    )
    MAX_COMPLAINT_LENGTH: int = Field(
        default=2000,
        ge=100,
        description="Maximum complaint text length"
    )
    ESCALATION_THRESHOLD_HOURS: int = Field(
        default=48,
        ge=1,
        description="Hours before auto-escalation"
    )
    
    # ==================== SPAM DETECTION ====================
    SPAM_KEYWORDS: List[str] = Field(
        default=["test", "dummy", "fake", "spam"],
        description="Keywords for spam detection"
    )
    MAX_COMPLAINTS_PER_HOUR: int = Field(
        default=5,
        ge=1,
        description="Maximum complaints per hour per student"
    )
    SPAM_THRESHOLD_SCORE: float = Field(
        default=0.7,
        ge=0.0,
        le=1.0,
        description="Threshold for spam classification"
    )
    
    # ==================== OPTIONAL: REDIS ====================
    REDIS_URL: Optional[str] = Field(
        default=None,
        description="Redis connection URL (optional)"
    )
    CACHE_ENABLED: bool = Field(
        default=False,
        description="Enable caching"
    )
    CACHE_TTL: int = Field(
        default=3600,
        ge=60,
        description="Cache TTL in seconds"
    )
    
    # ==================== VALIDATORS ====================
    
    @field_validator('CORS_ORIGINS', 'CORS_ALLOW_METHODS', 'CORS_ALLOW_HEADERS', 
                     'ALLOWED_IMAGE_EXTENSIONS', 'SPAM_KEYWORDS', mode='before')
    @classmethod
    def parse_list_from_string(cls, v):
        """Parse list from JSON string or comma-separated string"""
        if isinstance(v, str):
            # Try JSON first
            try:
                return json.loads(v)
            except json.JSONDecodeError:
                # Fall back to comma-separated
                return [item.strip() for item in v.split(',') if item.strip()]
        return v
    
    @field_validator('DATABASE_URL')
    @classmethod
    def validate_database_url(cls, v):
        """Ensure database URL uses asyncpg driver"""
        if not v.startswith('postgresql+asyncpg://'):
            raise ValueError(
                "DATABASE_URL must use asyncpg driver: "
                "postgresql+asyncpg://user:pass@host:port/db"
            )
        return v
    
    @field_validator('LOG_LEVEL')
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level"""
        allowed_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL']
        v_upper = v.upper()
        if v_upper not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v_upper
    
    @field_validator('LOG_FORMAT')
    @classmethod
    def validate_log_format(cls, v):
        """Validate log format"""
        allowed_formats = ['json', 'text']
        v_lower = v.lower()
        if v_lower not in allowed_formats:
            raise ValueError(f"LOG_FORMAT must be one of {allowed_formats}")
        return v_lower
    
    @field_validator('ENVIRONMENT')
    @classmethod
    def validate_environment(cls, v):
        """Validate environment"""
        allowed_envs = ['development', 'staging', 'production', 'test']
        v_lower = v.lower()
        if v_lower not in allowed_envs:
            raise ValueError(f"ENVIRONMENT must be one of {allowed_envs}")
        return v_lower
    
    # ==================== COMPUTED PROPERTIES ====================
    
    @computed_field
    @property
    def database_config(self) -> Dict:
        """Get database configuration dict"""
        return {
            "url": self.DATABASE_URL,
            "echo": self.DB_ECHO,
            "pool_size": self.DB_POOL_SIZE,
            "max_overflow": self.DB_MAX_OVERFLOW,
            "pool_timeout": self.DB_POOL_TIMEOUT,
            "pool_recycle": self.DB_POOL_RECYCLE,
            "pool_pre_ping": True,
        }
    
    @computed_field
    @property
    def jwt_config(self) -> Dict:
        """Get JWT configuration dict"""
        return {
            "secret_key": self.JWT_SECRET_KEY,
            "algorithm": self.JWT_ALGORITHM,
            "expiration_days": self.JWT_EXPIRATION_DAYS,
        }
    
    @computed_field
    @property
    def llm_config(self) -> Dict:
        """Get LLM configuration dict"""
        return {
            "api_key": self.GROQ_API_KEY,
            "model": self.LLM_MODEL,
            "temperature": self.LLM_TEMPERATURE,
            "max_tokens": self.LLM_MAX_TOKENS,
            "timeout": self.LLM_TIMEOUT,
            "max_retries": self.LLM_MAX_RETRIES,
        }
    
    @computed_field
    @property
    def priority_scores(self) -> Dict[str, int]:
        """Get priority score thresholds"""
        return {
            "Low": self.PRIORITY_LOW_MIN,
            "Medium": self.PRIORITY_MEDIUM_MIN,
            "High": self.PRIORITY_HIGH_MIN,
            "Critical": self.PRIORITY_CRITICAL_MIN,
        }
    
    @computed_field
    @property
    def is_production(self) -> bool:
        """Check if running in production"""
        return self.ENVIRONMENT == "production"
    
    @computed_field
    @property
    def is_development(self) -> bool:
        """Check if running in development"""
        return self.ENVIRONMENT == "development"
    
    # ==================== MODEL CONFIG ====================
    
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore",  # Ignore extra fields in .env
        validate_default=True,
    )


# ==================== CREATE GLOBAL INSTANCE ====================

settings = Settings()


# ==================== HELPER FUNCTIONS ====================

def get_settings() -> Settings:
    """
    Get settings instance (for dependency injection).
    
    Returns:
        Settings instance
    """
    return settings


# ==================== EXPORTS ====================

__all__ = ["settings", "Settings", "get_settings"]
