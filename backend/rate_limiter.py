"""
Simple rate limiter for API endpoints
"""
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, Tuple
from fastapi import HTTPException, Request


class RateLimiter:
    """Simple in-memory rate limiter"""
    
    def __init__(self):
        # Store: {identifier: [(timestamp, count)]}
        self.requests: Dict[str, list] = defaultdict(list)
        self.cleanup_interval = timedelta(hours=1)
        self.last_cleanup = datetime.now()
    
    def _cleanup_old_requests(self):
        """Remove old request records"""
        now = datetime.now()
        if now - self.last_cleanup > self.cleanup_interval:
            cutoff = now - timedelta(hours=1)
            for key in list(self.requests.keys()):
                self.requests[key] = [
                    (ts, count) for ts, count in self.requests[key]
                    if ts > cutoff
                ]
                if not self.requests[key]:
                    del self.requests[key]
            self.last_cleanup = now
    
    def check_rate_limit(
        self,
        identifier: str,
        max_requests: int,
        window_minutes: int
    ) -> bool:
        """
        Check if rate limit is exceeded
        
        Args:
            identifier: Unique identifier (e.g., IP address, user ID)
            max_requests: Maximum number of requests allowed
            window_minutes: Time window in minutes
        
        Returns:
            True if within limit, raises HTTPException if exceeded
        """
        self._cleanup_old_requests()
        
        now = datetime.now()
        window_start = now - timedelta(minutes=window_minutes)
        
        # Count requests in the current window
        recent_requests = [
            (ts, count) for ts, count in self.requests[identifier]
            if ts > window_start
        ]
        
        total_count = sum(count for _, count in recent_requests)
        
        if total_count >= max_requests:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded. Maximum {max_requests} requests per {window_minutes} minutes."
            )
        
        # Add current request
        self.requests[identifier].append((now, 1))
        
        return True
    
    def get_identifier(self, request: Request) -> str:
        """Get identifier from request (IP address)"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"


# Global rate limiter instance
rate_limiter = RateLimiter()


# Rate limit decorators
def rate_limit_login(request: Request):
    """Rate limit for login endpoint: 5 attempts per 15 minutes"""
    identifier = rate_limiter.get_identifier(request)
    rate_limiter.check_rate_limit(identifier, max_requests=5, window_minutes=15)


def rate_limit_register(request: Request):
    """Rate limit for registration: 3 attempts per hour"""
    identifier = rate_limiter.get_identifier(request)
    rate_limiter.check_rate_limit(identifier, max_requests=3, window_minutes=60)


def rate_limit_password_reset(request: Request):
    """Rate limit for password reset: 3 attempts per hour"""
    identifier = rate_limiter.get_identifier(request)
    rate_limiter.check_rate_limit(identifier, max_requests=3, window_minutes=60)


def rate_limit_invite(request: Request):
    """Rate limit for invites: 10 per hour"""
    identifier = rate_limiter.get_identifier(request)
    rate_limiter.check_rate_limit(identifier, max_requests=10, window_minutes=60)
