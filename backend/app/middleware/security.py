"""
Security middleware for additional security headers and rate limiting
"""

import time
import logging
from collections import defaultdict
from typing import Callable, Dict
from fastapi import Request, Response, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("app.security")


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Add security headers to all responses"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response"""
        response = await call_next(request)

        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"

        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self'; "
            "frame-ancestors 'none';"
        )
        response.headers["Content-Security-Policy"] = csp

        return response


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Simple in-memory rate limiting middleware
    For production, use Redis-based rate limiting (e.g., slowapi with Redis)
    """

    def __init__(
        self,
        app: ASGIApp,
        requests_per_minute: int = 60,
        burst_size: int = 100
    ):
        super().__init__(app)
        self.requests_per_minute = requests_per_minute
        self.burst_size = burst_size
        self.client_requests: Dict[str, list] = defaultdict(list)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Check rate limit and process request"""

        # Skip rate limiting for health check endpoint
        if request.url.path == "/api/v1/health":
            return await call_next(request)

        # Get client identifier
        client_ip = request.client.host if request.client else "unknown"
        current_time = time.time()

        # Clean old requests (older than 1 minute)
        cutoff_time = current_time - 60
        self.client_requests[client_ip] = [
            req_time for req_time in self.client_requests[client_ip]
            if req_time > cutoff_time
        ]

        # Check rate limit
        if len(self.client_requests[client_ip]) >= self.requests_per_minute:
            logger.warning(
                f"Rate limit exceeded for client {client_ip}: "
                f"{len(self.client_requests[client_ip])} requests in last minute"
            )
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please try again later.",
                headers={"Retry-After": "60"}
            )

        # Check burst limit
        recent_requests = [
            req_time for req_time in self.client_requests[client_ip]
            if req_time > current_time - 10  # Last 10 seconds
        ]
        if len(recent_requests) >= self.burst_size:
            logger.warning(
                f"Burst limit exceeded for client {client_ip}: "
                f"{len(recent_requests)} requests in last 10 seconds"
            )
            raise HTTPException(
                status_code=429,
                detail="Too many requests. Please slow down.",
                headers={"Retry-After": "10"}
            )

        # Record request
        self.client_requests[client_ip].append(current_time)

        # Process request
        response = await call_next(request)

        # Add rate limit headers
        remaining = self.requests_per_minute - len(self.client_requests[client_ip])
        response.headers["X-RateLimit-Limit"] = str(self.requests_per_minute)
        response.headers["X-RateLimit-Remaining"] = str(max(0, remaining))
        response.headers["X-RateLimit-Reset"] = str(int(current_time + 60))

        return response


class URLValidationMiddleware(BaseHTTPMiddleware):
    """Validate URLs to prevent SSRF attacks"""

    BLOCKED_HOSTS = {
        "localhost",
        "127.0.0.1",
        "0.0.0.0",
        "::1",
        "169.254.169.254",  # AWS metadata
        "metadata.google.internal",  # GCP metadata
    }

    BLOCKED_NETWORKS = [
        "10.",      # Private network
        "172.16.",  # Private network
        "172.17.",
        "172.18.",
        "172.19.",
        "172.20.",
        "172.21.",
        "172.22.",
        "172.23.",
        "172.24.",
        "172.25.",
        "172.26.",
        "172.27.",
        "172.28.",
        "172.29.",
        "172.30.",
        "172.31.",
        "192.168.", # Private network
    ]

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate request and process"""

        # Only validate POST requests to analysis endpoint
        if request.method == "POST" and "/analysis" in request.url.path:
            try:
                body = await request.body()
                # Re-populate request body for downstream handlers
                async def receive():
                    return {"type": "http.request", "body": body}
                request._receive = receive

                # Parse URL from request body if JSON
                if request.headers.get("content-type") == "application/json":
                    import json
                    try:
                        data = json.loads(body.decode())
                        url = data.get("url", "")
                        if url:
                            self._validate_url(url)
                    except json.JSONDecodeError:
                        pass  # Let FastAPI handle validation
            except Exception as e:
                logger.error(f"Error in URL validation: {e}")

        return await call_next(request)

    def _validate_url(self, url: str):
        """Check if URL is safe to crawl"""
        from urllib.parse import urlparse

        parsed = urlparse(url)
        hostname = parsed.hostname

        if not hostname:
            return

        # Check blocked hosts
        if hostname.lower() in self.BLOCKED_HOSTS:
            logger.warning(f"Blocked SSRF attempt: {url}")
            raise HTTPException(
                status_code=400,
                detail="Invalid URL: Cannot access local or private addresses"
            )

        # Check blocked networks
        for network in self.BLOCKED_NETWORKS:
            if hostname.startswith(network):
                logger.warning(f"Blocked private network access: {url}")
                raise HTTPException(
                    status_code=400,
                    detail="Invalid URL: Cannot access private network addresses"
                )
