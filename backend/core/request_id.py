"""Request-ID middleware for FieldMind.

Attaches a unique ``X-Request-ID`` header to every incoming request so that
logs emitted during that request can be correlated even across multiple
concurrent requests.  The ID is propagated to response headers as well.
"""
from __future__ import annotations

import uuid
from contextvars import ContextVar

from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.requests import Request
from starlette.responses import Response

# Module-level ContextVar so any code path can read the current request ID
# without having to thread the value through every function call.
_request_id_var: ContextVar[str] = ContextVar("request_id", default="")


def get_request_id() -> str:
    """Return the request ID for the currently executing async task."""
    return _request_id_var.get()


class RequestIDMiddleware(BaseHTTPMiddleware):
    """Attach and propagate a ``X-Request-ID`` to every HTTP request."""

    HEADER = "X-Request-ID"

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        # Re-use an incoming ID (useful when a proxy forwards its own IDs)
        request_id = request.headers.get(self.HEADER) or str(uuid.uuid4())
        token = _request_id_var.set(request_id)

        try:
            response: Response = await call_next(request)
        finally:
            _request_id_var.reset(token)

        response.headers[self.HEADER] = request_id
        return response
