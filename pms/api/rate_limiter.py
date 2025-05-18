"""Rate limiter for PubMed API requests."""

import time
import logging
from typing import Callable, Any

logger = logging.getLogger(__name__)


class RateLimiter:
    """Rate limiter for API requests."""

    def __init__(self, requests_per_second: float) -> None:
        """Initialize the rate limiter.

        Args:
            requests_per_second: Maximum number of requests per second
        """
        self.min_interval = 1.0 / requests_per_second
        self.last_request_time = 0.0

    def wait(self) -> None:
        """Wait until it's safe to make another request."""
        now = time.time()
        elapsed = now - self.last_request_time

        if elapsed < self.min_interval:
            sleep_time = self.min_interval - elapsed
            logger.debug(f"Rate limiting: sleeping for {sleep_time:.2f}s")
            time.sleep(sleep_time)

        self.last_request_time = time.time()

    def __call__(self, func: Callable) -> Callable:
        """Decorator for rate-limited functions.

        Args:
            func: Function to decorate

        Returns:
            Decorated function
        """

        def wrapper(*args: Any, **kwargs: Any) -> Any:
            self.wait()
            return func(*args, **kwargs)

        return wrapper
