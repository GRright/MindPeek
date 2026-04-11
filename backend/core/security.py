"""
安全中间件和工具函数
"""
import time
import re
from fastapi import Request, HTTPException
from starlette.middleware.base import BaseHTTPMiddleware
from collections import defaultdict
from backend.core.config import settings


class RateLimiter:
    def __init__(self, max_requests: int, window_seconds: int):
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests = defaultdict(list)
    
    def is_allowed(self, client_id: str) -> bool:
        now = time.time()
        window_start = now - self.window_seconds
        
        self.requests[client_id] = [
            req_time for req_time in self.requests[client_id]
            if req_time > window_start
        ]
        
        if len(self.requests[client_id]) >= self.max_requests:
            return False
        
        self.requests[client_id].append(now)
        return True


rate_limiter = RateLimiter(
    max_requests=settings.rate_limit_requests,
    window_seconds=settings.rate_limit_window
)


def sanitize_input(text: str) -> str:
    if not text:
        return text
    
    dangerous_patterns = [
        r'<script[^>]*>.*?</script>',
        r'javascript:',
        r'on\w+="[^"]*"',
        r'on\w+=\'[^\']*\'',
        r'on\w+=[^\s>]+',
        r'eval\s*\(',
        r'document\.',
        r'window\.',
    ]
    
    sanitized = text
    for pattern in dangerous_patterns:
        sanitized = re.sub(pattern, '', sanitized, flags=re.IGNORECASE | re.DOTALL)
    
    return sanitized


def validate_user_id(user_id: str) -> bool:
    if not user_id or len(user_id) > 100:
        return False
    if not re.match(r'^[a-zA-Z0-9_\-]+$', user_id):
        return False
    return True


def validate_message(message: str) -> bool:
    if not message or len(message) > 5000:
        return False
    return True


def validate_feature_type(feature_type: str) -> bool:
    if not feature_type or len(feature_type) > 100:
        return False
    if not re.match(r'^[\w\u4e00-\u9fa5]+$', feature_type):
        return False
    return True


def validate_feature_value(feature_value: str) -> bool:
    if not feature_value or len(feature_value) > 1000:
        return False
    return True


def validate_provider(provider: str) -> bool:
    if not provider or len(provider) > 50:
        return False
    if not re.match(r'^[a-zA-Z0-9_\-]+$', provider):
        return False
    return True


def validate_api_key(api_key: str) -> bool:
    if not api_key or len(api_key) > 500:
        return False
    return True


def validate_model(model: str) -> bool:
    if not model or len(model) > 100:
        return False
    if not re.match(r'^[a-zA-Z0-9_\-\.]+$', model):
        return False
    return True


def validate_api_url(api_url: str) -> bool:
    if not api_url:
        return True
    if len(api_url) > 500:
        return False
    if not re.match(r'^https?://', api_url):
        return False
    return True


def validate_limit(limit: int) -> bool:
    if not isinstance(limit, int) or limit < 1 or limit > 500:
        return False
    return True


def validate_threshold(threshold: float) -> bool:
    if not isinstance(threshold, (int, float)) or threshold < 0 or threshold > 1:
        return False
    return True


def validate_session_id(session_id: str) -> bool:
    if not session_id:
        return True
    if len(session_id) > 100:
        return False
    if not re.match(r'^[a-zA-Z0-9_\-]+$', session_id):
        return False
    return True


class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        if not settings.rate_limit_enabled:
            return await call_next(request)
        
        client_ip = request.client.host if request.client else "unknown"
        
        if not rate_limiter.is_allowed(client_ip):
            raise HTTPException(
                status_code=429,
                detail="请求过于频繁，请稍后再试"
            )
        
        return await call_next(request)
