from skills.clean_compressed_sitemap_parser_v3 import (
    CleanCompressedSitemapParserV3,
    CleanCompressedSitemapParserError
)
from skills.rate_limiter import RateLimiter, RateLimitExceeded


class ResilientCleanCompressedSitemapParserError(Exception):
    """Исключение для отказоустойчивого парсера сайтмапов."""
    pass


class ResilientCleanCompressedSitemapParser:
    def __init__(self, db_path: str = ":memory:", calls: int = 10, period: float = 1.0, raise_on_limit: bool = True):
        self.db_path = db_path
        self.rate_limiter = RateLimiter(calls=calls, period=period, raise_on_limit=raise_on_limit)
        self.parser_v3 = CleanCompressedSitemapParserV3(db_path=db_path)

    def parse(self, url: str, timeout: int = 5):
        self.rate_limiter.acquire()
        try:
            return self.parser_v3.parse(url, timeout)
        except RateLimitExceeded:
            raise
        except Exception as e:
            raise ResilientCleanCompressedSitemapParserError(str(e)) from e

    def parse_and_clean(self, url: str, timeout: int = 5):
        self.rate_limiter.acquire()
        try:
            return self.parser_v3.parse_and_clean(url, timeout)
        except RateLimitExceeded:
            raise
        except Exception as e:
            raise ResilientCleanCompressedSitemapParserError(str(e)) from e

    def validate_sitemap(self, url: str, timeout: int = 5) -> bool:
        self.rate_limiter.acquire()
        try:
            result = self.parser_v3.validate_sitemap(url, timeout)
            if isinstance(result, tuple):
                return bool(result[0])
            return bool(result)
        except RateLimitExceeded:
            raise
        except Exception:
            return False


def resilient_clean_compressed_sitemap_parser_flow(url: str, timeout: int = 5, db_path: str = ":memory:"):
    parser = ResilientCleanCompressedSitemapParser(db_path=db_path)
    try:
        return parser.parse_and_clean(url, timeout)
    except RateLimitExceeded:
        raise
    except Exception as e:
        raise ResilientCleanCompressedSitemapParserError(str(e)) from e