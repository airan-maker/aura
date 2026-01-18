"""FastAPI main application."""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from app.config import settings
from app.api.v1 import health, analysis, competitive
from app.core.logging import setup_logging
from app.middleware.logging import LoggingMiddleware
from app.middleware.security import (
    SecurityHeadersMiddleware,
    RateLimitMiddleware,
    URLValidationMiddleware
)
from app.middleware.error_handler import (
    http_exception_handler,
    validation_exception_handler,
    general_exception_handler
)

# Setup logging
setup_logging()

# Create FastAPI app
app = FastAPI(
    title="Aura API",
    description="차세대 SEO & AEO 통합 분석 플랫폼",
    version="1.0.0",
    docs_url="/docs" if settings.ENVIRONMENT != "production" else None,
    redoc_url="/redoc" if settings.ENVIRONMENT != "production" else None,
    redirect_slashes=False  # Prevent redirect that loses CORS headers
)

# Add middleware (order matters - last added = first executed)
# CORS must be added LAST (executes FIRST) to handle preflight requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins_list,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Security and other middleware
app.add_middleware(SecurityHeadersMiddleware)
app.add_middleware(URLValidationMiddleware)
app.add_middleware(RateLimitMiddleware, requests_per_minute=60, burst_size=100)
app.add_middleware(LoggingMiddleware)

# Exception handlers
app.add_exception_handler(StarletteHTTPException, http_exception_handler)
app.add_exception_handler(RequestValidationError, validation_exception_handler)
app.add_exception_handler(Exception, general_exception_handler)

# Include routers
app.include_router(health.router, prefix="/api/v1")
app.include_router(analysis.router, prefix="/api/v1")
app.include_router(competitive.router, prefix="/api/v1")


@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Welcome to Aura API",
        "docs": "/docs",
        "version": "1.0.0"
    }
