"""
Logging middleware for request/response tracking
"""

import time
import logging
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp

logger = logging.getLogger("app.middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware to log all requests and responses"""

    def __init__(self, app: ASGIApp):
        super().__init__(app)

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Process request and log details"""

        # Start timer
        start_time = time.time()

        # Get request details
        method = request.method
        url = str(request.url)
        client = request.client.host if request.client else "unknown"

        # Log request
        logger.info(f"Request started: {method} {url} from {client}")

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration = time.time() - start_time

            # Log response
            logger.info(
                f"Request completed: {method} {url} "
                f"status={response.status_code} duration={duration:.3f}s"
            )

            return response

        except Exception as e:
            # Calculate duration
            duration = time.time() - start_time

            # Log error
            logger.error(
                f"Request failed: {method} {url} "
                f"error={str(e)} duration={duration:.3f}s",
                exc_info=True
            )

            raise
