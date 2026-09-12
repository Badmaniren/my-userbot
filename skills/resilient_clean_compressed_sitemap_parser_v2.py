import logging
from skills.resilient_clean_compressed_sitemap_parser import ResilientCleanCompressedSitemapParser
from skills.memory_profiler import assert_memory_limit
from skills.rate_limiter import RateLimiter

logger = logging.getLogger(__name__)

class ResilientCleanCompressedSitemapParserV2Error(Exception):
    """Кастомное исключение для парсера sitemap v2."""
    pass

class ResilientCleanCompressedSitemapParserV2(ResilientCleanCompressedSitemapParser):
    """
    Отказоустойчивый, очищенный и сжатый парсер sitemap версии 2.
    Композитно наследуется от ResilientCleanCompressedSitemapParser, добавляя
    проверку лимитов памяти, rate limiter и логирование.
    """

    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=1.0, raise_on_limit=True):
        super().__init__(db_path=db_path)
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.raise_on_limit = raise_on_limit
        self.rate_limiter = RateLimiter(calls=calls, period=period)
        logger.info(f"Initialized ResilientCleanCompressedSitemapParserV2 with db={db_path}, max_mem={max_memory_mb}MB")

    def _check_memory(self):
        try:
            assert_memory_limit(self.max_memory_mb)
        except Exception as e:
            if self.raise_on_limit:
                raise
            logger.error(f"Memory limit exceeded: {e}")

    def parse(self, url, timeout=10, **kwargs):
        self._check_memory()
        with self.rate_limiter:
            logger.info(f"Parsing sitemap with rate limiter: {url}")
            return super().parse(url, timeout, **kwargs)

    def parse_and_clean(self, url, timeout=10, **kwargs):
        self._check_memory()
        with self.rate_limiter:
            logger.info(f"Parsing and cleaning sitemap with rate limiter: {url}")
            return super().parse_and_clean(url, timeout, **kwargs)

    def validate_sitemap(self, url, timeout=10, **kwargs):
        self._check_memory()
        with self.rate_limiter:
            logger.info(f"Validating sitemap with rate limiter: {url}")
            result = super().validate_sitemap(url, timeout, **kwargs)
            if isinstance(result, tuple):
                return bool(result[0])
            return bool(result)