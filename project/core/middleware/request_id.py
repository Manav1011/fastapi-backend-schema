from __future__ import annotations

import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response


class RequestIdMiddleware(BaseHTTPMiddleware):
    header_name = "X-Request-ID"

    async def dispatch(self, request: Request, call_next) -> Response:
        req_id = request.headers.get(self.header_name) or str(uuid.uuid4())
        request.state.request_id = req_id

        response = await call_next(request)
        response.headers[self.header_name] = req_id
        return response


