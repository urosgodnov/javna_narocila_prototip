"""
Rate limiter for SWIFT/BIC lookups to prevent data harvesting.
Story 3.2: SWIFT/BIC Validation and Registry Lookup
"""

import time
from typing import Dict, Tuple
from collections import defaultdict


class RateLimiter:
    """Session-based rate limiter for SWIFT lookups."""
    
    def __init__(self, max_requests: int = 10, window_seconds: int = 60):
        """Initialize rate limiter.
        
        Args:
            max_requests: Maximum requests allowed per window
            window_seconds: Time window in seconds
        """
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self.requests: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, session_id: str) -> Tuple[bool, str]:
        """Check if request is allowed for session.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Tuple of (is_allowed, error_message)
        """
        current_time = time.time()
        
        # Clean old requests
        self.requests[session_id] = [
            req_time for req_time in self.requests[session_id]
            if current_time - req_time < self.window_seconds
        ]
        
        # Check rate limit
        if len(self.requests[session_id]) >= self.max_requests:
            wait_time = self.window_seconds - (current_time - self.requests[session_id][0])
            return False, f"Preveč poizvedb. Počakajte {int(wait_time)} sekund."
        
        # Record request
        self.requests[session_id].append(current_time)
        return True, ""
    
    def get_remaining_requests(self, session_id: str) -> int:
        """Get remaining requests for session.
        
        Args:
            session_id: Unique session identifier
        
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        self.requests[session_id] = [
            req_time for req_time in self.requests[session_id]
            if current_time - req_time < self.window_seconds
        ]
        return max(0, self.max_requests - len(self.requests[session_id]))
    
    def reset_session(self, session_id: str):
        """Reset rate limit for a specific session.
        
        Args:
            session_id: Session to reset
        """
        if session_id in self.requests:
            del self.requests[session_id]


# Global rate limiter instance for SWIFT lookups
swift_rate_limiter = RateLimiter(max_requests=10, window_seconds=60)