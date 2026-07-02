"""Request sanitization middleware."""

import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class InputSanitizationMiddleware(BaseHTTPMiddleware):
    """Strip null bytes and dangerous control characters from JSON request bodies.

    Runs before Pydantic validation so that downstream code never sees
    null bytes or embedded control characters.
    """

    async def dispatch(self, request: Request, call_next):
        # Only sanitize JSON request bodies
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type and request.method in ("POST", "PUT", "PATCH"):
            return await call_next(request)

        body = await request.body()
        if body:
            sanitized = _sanitize_bytes(body)
            # Replace the body so downstream receivers get sanitized data
            request._body = sanitized

        response = await call_next(request)
        return response


def _sanitize_bytes(data: bytes) -> bytes:
    """Remove null bytes and control characters (except normal whitespace) from data."""
    # Remove null bytes
    cleaned = data.replace(b"\x00", b"")
    # Remove control characters 0x01-0x08, 0x0B-0x0C, 0x0E-0x1F
    # Keep: \t (0x09), \n (0x0A), \r (0x0D)
    pattern = re.compile(rb"[\x01-\x08\x0b\x0c\x0e-\x1f]")
    return pattern.sub(b"", cleaned)
