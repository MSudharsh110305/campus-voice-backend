"""
API package initialization.
FastAPI application setup and route registration.
"""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from src.config.settings import settings
from src.middleware import setup_middleware
from src.api.routes import create_api_router
from src.utils.logger import app_logger
from src.utils.exceptions import CampusVoiceException, to_http_exception


def create_app() -> FastAPI:
    """
    Create and configure FastAPI application.
    
    Returns:
        Configured FastAPI application
    """
    # Create FastAPI app
    app = FastAPI(
        title="CampusVoice API",
        description="Campus Complaint Management System with AI-powered categorization",
        version="1.0.0",
        docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
        redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
        openapi_url="/openapi.json" if settings.ENVIRONMENT != "production" else None,
    )
    
    # Setup middleware
    setup_middleware(app)
    
    # Register routes
    api_router, root_router = create_api_router()
    app.include_router(api_router)
    app.include_router(root_router)
    
    # Setup exception handlers
    setup_exception_handlers(app)
    
    # Startup event
    @app.on_event("startup")
    async def startup_event():
        """Execute on application startup."""
        app_logger.info(f"Starting CampusVoice API in {settings.ENVIRONMENT} mode")
        app_logger.info(f"Database: {settings.DATABASE_URL.split('@')[1] if '@' in settings.DATABASE_URL else 'SQLite'}")
        app_logger.info(f"CORS Origins: {settings.CORS_ORIGINS}")
    
    # Shutdown event
    @app.on_event("shutdown")
    async def shutdown_event():
        """Execute on application shutdown."""
        app_logger.info("Shutting down CampusVoice API")
    
    # Root endpoint
    @app.get("/", tags=["Root"])
    async def root():
        """Root endpoint with API information."""
        return {
            "service": "CampusVoice API",
            "version": "1.0.0",
            "status": "running",
            "docs": "/docs" if settings.ENVIRONMENT != "production" else "disabled",
            "health": "/health"
        }
    
    return app


def setup_exception_handlers(app: FastAPI):
    """
    Setup global exception handlers.
    
    Args:
        app: FastAPI application
    """
    
    @app.exception_handler(CampusVoiceException)
    async def campus_voice_exception_handler(request: Request, exc: CampusVoiceException):
        """Handle CampusVoiceException."""
        http_exc = to_http_exception(exc)
        request_id = getattr(request.state, "request_id", "unknown")
        
        app_logger.warning(
            f"Application error | "
            f"ID: {request_id} | "
            f"Code: {exc.error_code} | "
            f"Message: {exc.message}"
        )
        
        return JSONResponse(
            status_code=http_exc.status_code,
            content={
                "success": False,
                "error": exc.message,
                "error_code": exc.error_code,
                "details": exc.details,
                "request_id": request_id
            }
        )
    
    @app.exception_handler(StarletteHTTPException)
    async def http_exception_handler(request: Request, exc: StarletteHTTPException):
        """Handle HTTPException."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        return JSONResponse(
            status_code=exc.status_code,
            content={
                "success": False,
                "error": exc.detail,
                "error_code": f"HTTP_{exc.status_code}",
                "request_id": request_id
            }
        )
    
    @app.exception_handler(RequestValidationError)
    async def validation_exception_handler(request: Request, exc: RequestValidationError):
        """Handle validation errors."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        errors = []
        for error in exc.errors():
            errors.append({
                "field": ".".join(str(x) for x in error["loc"][1:]),
                "message": error["msg"],
                "type": error["type"]
            })
        
        app_logger.warning(
            f"Validation error | "
            f"ID: {request_id} | "
            f"Errors: {errors}"
        )
        
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "success": False,
                "error": "Validation error",
                "error_code": "VALIDATION_ERROR",
                "details": {"validation_errors": errors},
                "request_id": request_id
            }
        )
    
    @app.exception_handler(Exception)
    async def global_exception_handler(request: Request, exc: Exception):
        """Handle all unhandled exceptions."""
        request_id = getattr(request.state, "request_id", "unknown")
        
        app_logger.error(
            f"Unhandled exception | "
            f"ID: {request_id} | "
            f"Type: {type(exc).__name__} | "
            f"Message: {str(exc)}",
            exc_info=True
        )
        
        # In production, don't expose internal errors
        if settings.ENVIRONMENT == "production":
            error_message = "Internal server error"
        else:
            error_message = str(exc)
        
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "error": error_message,
                "error_code": "INTERNAL_ERROR",
                "request_id": request_id
            }
        )


# Create application instance
app = create_app()


__all__ = ["app", "create_app"]
