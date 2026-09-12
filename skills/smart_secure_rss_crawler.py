from skills.secure_clean_compressed_rss_archiver import SecureCleanCompressedRSSArchiver
from skills.smart_crawler import SmartCrawler
from skills.rate_limiter import RateLimiter, RateLimitExceeded


class SmartSecureRSSCrawlerError(Exception):
    """Исключение для ошибок интеллектуального защищенного RSS-краулера."""
    pass


class SmartSecureRSSCrawler:
    def __init__(
        self,
        db_path=":memory:",
        max_memory_mb=128,
        calls=10,
        period=60,
        raise_on_limit=True
    ):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit

        self.archiver = SecureCleanCompressedRSSArchiver(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb
        )
        self.crawler = SmartCrawler()
        self.rate_limiter = RateLimiter(
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def archive_feed(self, url, timeout=10, force_refresh=False):
        try:
            self.rate_limiter.acquire()
            # Исправлено: убрана передача 'headers', так как LinkExtractor.extract не поддерживает этот аргумент
            self.crawler.coordinate_expansion(url)
            result = self.archiver.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
            return bool(result)
        except RateLimitExceeded as e:
            if self.raise_on_limit:
                raise SmartSecureRSSCrawlerError(str(e))
            return False
        except Exception as e:
            if not self.raise_on_limit:
                return False
            raise SmartSecureRSSCrawlerError(str(e))

    def get_archived_feed(self, url):
        # Возвращаем результат напрямую, чтобы тесты могли корректно его проверить
        return self.archiver.get_archived_feed(url)

    def coordinate_expansion(self, url):
        return self.crawler.coordinate_expansion(url)


def smart_secure_rss_crawler_flow(
    url,
    timeout=10,
    db_path=":memory:",
    max_memory_mb=128,
    force_refresh=False,
    calls=10,
    period=60,
    raise_on_limit=True
):
    crawler = SmartSecureRSSCrawler(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.archive_feed(url, timeout=timeout, force_refresh=force_refresh)