from skills.secure_clean_compressed_rss_archiver import SecureCleanCompressedRSSArchiver as BaseArchiver
from skills.resilient_rss_fetcher import ResilientRSSFetcher


class SecureCleanCompressedRSSArchiverError(Exception):
    """Пользовательское исключение для ошибок архиватора RSS."""
    pass


class SecureCleanCompressedRSSArchiver:
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
        self.fetcher = ResilientRSSFetcher(calls=calls, period=period, raise_on_limit=raise_on_limit)
        self.base_archiver = BaseArchiver(db_path=db_path, max_memory_mb=max_memory_mb)
        self.resilient_rss_fetcher = self.fetcher

    def archive_feed(self, url, timeout=5, force_refresh=False):
        try:
            feed_data = self.fetcher.fetch(url, timeout=timeout)
            if feed_data is None:
                return False
            result = self.base_archiver.archive_feed(url, feed_data)
            return bool(result) if result is not None else True
        except Exception as e:
            if self.raise_on_limit:
                raise SecureCleanCompressedRSSArchiverError(str(e))
            return False

    def get_archived_feed(self, url):
        return self.base_archiver.get_archived_feed(url)


class ResilientSecureCleanCompressedRSSArchiver(SecureCleanCompressedRSSArchiver):
    pass


def secure_clean_compressed_rss_archive_flow(
    url,
    timeout=5,
    db_path=":memory:",
    max_memory_mb=128,
    force_refresh=False,
    calls=10,
    period=60,
    raise_on_limit=True
):
    archiver = SecureCleanCompressedRSSArchiver(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    res = archiver.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
    return bool(res) if res is not None else True


def resilient_secure_clean_compressed_rss_archive_flow(
    url,
    timeout=5,
    db_path=":memory:",
    max_memory_mb=128,
    force_refresh=False,
    calls=10,
    period=60,
    raise_on_limit=True
):
    return secure_clean_compressed_rss_archive_flow(
        url=url,
        timeout=timeout,
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        force_refresh=force_refresh,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )