import sys
from skills.resilient_clean_compressed_sitemap_parser_v2 import ResilientCleanCompressedSitemapParserV2
from skills.headers_rotator import HeadersRotator
from skills.rate_limiter import RateLimiter
from skills.memory_profiler import assert_memory_limit

class ResilientSecureCleanCompressedSitemapParserV2Error(Exception):
    """Кастомное исключение для парсера v2."""
    pass

class ResilientSecureCleanCompressedSitemapParserV2:
    def __init__(self, db_path=":memory:", max_memory_mb=100, calls=10, period=60, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        
        self.parser = ResilientCleanCompressedSitemapParserV2()
        self.headers_rotator = HeadersRotator()
        self.rate_limiter = RateLimiter(calls=calls, period=period)

    def _prepare_request(self, url: str):
        assert_memory_limit(self.max_memory_mb)
        self.rate_limiter.acquire()
        self.headers_rotator.rotate_headers()

    def parse(self, url: str, timeout: int = 5):
        try:
            self._prepare_request(url)
            return self.parser.parse(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureCleanCompressedSitemapParserV2Error):
                raise
            raise ResilientSecureCleanCompressedSitemapParserV2Error(str(e)) from e

    def parse_and_clean(self, url: str, timeout: int = 5):
        try:
            self._prepare_request(url)
            return self.parser.parse_and_clean(url, timeout)
        except Exception as e:
            if isinstance(e, ResilientSecureCleanCompressedSitemapParserV2Error):
                raise
            raise ResilientSecureCleanCompressedSitemapParserV2Error(str(e)) from e

    def validate_sitemap(self, url: str, timeout: int = 5) -> bool:
        try:
            assert_memory_limit(self.max_memory_mb)
            self.rate_limiter.acquire()
            self.headers_rotator.rotate_headers()
            
            headers_valid = True
            if hasattr(self.headers_rotator, 'validate_headers_against_target'):
                headers_valid = bool(self.headers_rotator.validate_headers_against_target(url))
                
            parser_valid = bool(self.parser.validate_sitemap(url, timeout))
            return headers_valid and parser_valid
        except Exception as e:
            if self.raise_on_limit and "Memory limit" in str(e):
                raise
            return False