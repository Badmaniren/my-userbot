import time
import threading
from collections import deque

class RateLimitExceeded(Exception):
    """Исключение, вызываемое при превышении лимита запросов."""
    pass

class RateLimiter:
    """Модуль контроля частоты запросов (Rate Limiter) с поддержкой контекстного менеджера и потокобезопасности."""

    def __init__(self, calls: int, period: float, raise_on_limit: bool = False):
        if not isinstance(calls, (int, float)) or not isinstance(period, (int, float)):
            raise TypeError("Calls and period must be numbers")
        
        if isinstance(calls, bool) or isinstance(period, bool):
            raise TypeError("Calls and period cannot be booleans")

        if calls <= 0:
            raise ValueError("Calls must be greater than 0")
        if period <= 0:
            raise ValueError("Period must be greater than 0")

        self.calls = int(calls)
        self.period = float(period)
        self.raise_on_limit = raise_on_limit
        self.timestamps = deque()
        self.lock = threading.Lock()

    def acquire(self):
        with self.lock:
            now = time.time()
            
            while self.timestamps and self.timestamps[0] <= now - self.period:
                self.timestamps.popleft()

            if len(self.timestamps) >= self.calls:
                if self.raise_on_limit:
                    raise RateLimitExceeded("Rate limit exceeded")
                else:
                    sleep_time = self.timestamps[0] + self.period - now
                    if sleep_time > 0:
                        time.sleep(sleep_time)
                    
                    now = time.time()
                    while self.timestamps and self.timestamps[0] <= now - self.period:
                        self.timestamps.popleft()

            self.timestamps.append(time.time())

    def __enter__(self):
        self.acquire()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass