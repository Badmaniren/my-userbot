import io
import requests
from skills.smart_secure_compressed_rss_crawler import (
    SmartSecureCompressedRSSCrawler,
    SmartSecureCompressedRSSCrawlerError
)
from skills.resilient_rss_fetcher import ResilientRSSFetcher


class SmartSecureCompressedRSSCrawlerV2Error(Exception):
    """Кастомное исключение для SmartSecureCompressedRSSCrawlerV2."""
    pass


class SmartSecureCompressedRSSCrawlerV2(SmartSecureCompressedRSSCrawler):
    """Эволюционировавший интеллектуальный защищенный RSS-краулер версии 2."""

    def __init__(self, db_path=":memory:", max_memory_mb=128, calls=5, period=60, raise_on_limit=True):
        super().__init__(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )
        self.resilient_fetcher = ResilientRSSFetcher(
            db_path=db_path,
            max_memory_mb=max_memory_mb,
            calls=calls,
            period=period,
            raise_on_limit=raise_on_limit
        )

    def archive_feed(self, url, timeout=10, force_refresh=False):
        try:
            return super().archive_feed(url, timeout=timeout, force_refresh=force_refresh)
        except SmartSecureCompressedRSSCrawlerV2Error:
            raise
        except Exception as e:
            raise SmartSecureCompressedRSSCrawlerV2Error(f"Ошибка архивации в V2: {e}") from e


def smart_secure_compressed_rss_crawler_v2_flow(
    url,
    timeout=10,
    db_path=":memory:",
    max_memory_mb=128,
    force_refresh=False,
    calls=5,
    period=60,
    raise_on_limit=True
):
    """Функция потока для SmartSecureCompressedRSSCrawlerV2."""
    crawler = SmartSecureCompressedRSSCrawlerV2(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return crawler.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
