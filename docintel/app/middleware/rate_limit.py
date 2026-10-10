"""
Simple sliding-window rate limiter backed by Redis, applied per authenticated
user (falls back to client IP for unauthenticated requests like /auth/login).
Protects the free Gemini quota and the API generally from abuse.
"""
import time

from fastapi import Request, status
from fastapi.responses import JSONResponse
from jose import JWTError, jwt
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.config import settings
from app.core.redis_client import get_redis_client


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if request.url.path in ("/health", "/docs", "/openapi.json", "/redoc"):
            return await call_next(request)

        identifier = self._get_identifier(request)
        redis_client = get_redis_client()

        window_key = f"ratelimit:{identifier}:{int(time.time() // 60)}"
        current_count = await redis_client.incr(window_key)
        if current_count == 1:
            await redis_client.expire(window_key, 60)

        if current_count > settings.RATE_LIMIT_PER_MINUTE:
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={"detail": "Rate limit exceeded. Please slow down."},
                headers={"Retry-After": "60"},
            )

        response = await call_next(request)
        response.headers["X-RateLimit-Limit"] = str(settings.RATE_LIMIT_PER_MINUTE)
        response.headers["X-RateLimit-Remaining"] = str(max(0, settings.RATE_LIMIT_PER_MINUTE - current_count))
        return response

    @staticmethod
    def _get_identifier(request: Request) -> str:
        """
        Prefer the actual user ID decoded from the JWT (stable across
        restarts, correctly groups all of one user's requests regardless of
        which token they're currently using). Falls back to client IP for
        unauthenticated requests, or if the token is malformed/expired —
        rate limiting is a defense mechanism, not an auth check, so we don't
        reject here even on a bad token.
        """
        auth_header = request.headers.get("authorization", "")
        if auth_header.startswith("Bearer "):
            token = auth_header.removeprefix("Bearer ").strip()
            try:
                # Decode without verifying expiry/signature strictly for rate-limiting
                # purposes only — a forged token still just gets its own IP-shared bucket,
                # it can't forge someone else's identity into a *higher* limit.
                payload = jwt.decode(
                    token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM],
                    options={"verify_exp": False},
                )
                user_id = payload.get("sub")
                if user_id:
                    return f"user:{user_id}"
            except JWTError:
                pass

        client_ip = request.client.host if request.client else "unknown"
        return f"ip:{client_ip}"