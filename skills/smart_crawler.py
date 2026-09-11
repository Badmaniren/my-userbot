import urllib.error
from skills import cached_ping, link_extractor
from skills.headers_rotator import HeadersRotator
from skills.rate_limiter import RateLimiter


class CrawlerError(Exception):
    pass


class RateLimitExceeded(Exception):
    pass


class MemoryLimitExceeded(Exception):
    pass


class JsonExtractorError(Exception):
    pass


class SmartCrawler:
    def __init__(self):
        self.headers_rotator = HeadersRotator()
        self.rate_limiter = RateLimiter(calls=5, period=1)
        self.link_extractor = link_extractor.LinkExtractor()

    def coordinate_expansion(self, url: str, timeout: int = 5):
        if not isinstance(url, str):
            raise TypeError("URL must be a string")

        headers = self.headers_rotator.rotate_headers()
        self.rate_limiter.acquire()

        ping_result = cached_ping.ping_and_cache(url, timeout=timeout)
        
        if not ping_result:
            raise CrawlerError("Target unresponsive")

        extracted_data = self.link_extractor.extract(url, headers=headers, timeout=timeout)
        return extracted_data