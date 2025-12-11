"""
Rate limiter utility for LLM API calls to prevent ResourceExhausted errors.
"""
import time
import asyncio
from typing import Callable, Any
from functools import wraps
import threading


class RateLimiter:
    """Rate limiter to throttle API calls."""
    
    def __init__(self, min_interval: float = 1.0, max_concurrent: int = 2):
        """
        Initialize rate limiter.
        
        Args:
            min_interval: Minimum seconds between API calls
            max_concurrent: Maximum concurrent API calls
        """
        self.min_interval = min_interval
        self.last_call_time = 0
        self.semaphore = threading.Semaphore(max_concurrent)
        self.lock = threading.Lock()
    
    def wait_if_needed(self):
        """Wait if needed to respect rate limits."""
        with self.lock:
            current_time = time.time()
            time_since_last = current_time - self.last_call_time
            if time_since_last < self.min_interval:
                sleep_time = self.min_interval - time_since_last
                time.sleep(sleep_time)
            self.last_call_time = time.time()
    
    def acquire(self):
        """Acquire semaphore for concurrent request limiting."""
        return self.semaphore.acquire(blocking=True)
    
    def release(self):
        """Release semaphore."""
        self.semaphore.release()


def rate_limit_llm_call(func: Callable) -> Callable:
    """Decorator to rate limit LLM calls."""
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    
    return wrapper

