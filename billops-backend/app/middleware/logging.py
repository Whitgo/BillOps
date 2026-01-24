import logging
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = logging.getLogger("request")
        logger.info("%s %s", request.method, request.url.path)
        response = await call_next(request)
        logger.info("%s %s %s", request.method, request.url.path, response.status_code)
        return response
