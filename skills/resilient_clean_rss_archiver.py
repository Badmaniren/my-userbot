from skills.resilient_rss_fetcher import ResilientRSSFetcher
from skills.clean_compressed_db_storage import CleanCompressedDBStorage


class ResilientCleanRSSArchiverError(Exception):
    """Кастомное исключение для ошибок архиватора RSS."""
    pass


class ResilientCleanRSSArchiver:
    def __init__(self, db_path=None, max_memory_mb=128, calls=5, period=60, raise_on_limit=False):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.fetcher = ResilientRSSFetcher(calls=calls, period=period, raise_on_limit=raise_on_limit)
        try:
            self.storage = CleanCompressedDBStorage(db_path=db_path, max_memory_mb=max_memory_mb)
        except TypeError:
            self.storage = CleanCompressedDBStorage(db_path=db_path)

    def archive_feed(self, url: str, timeout: int = 10, force_refresh: bool = False) -> bool:
        try:
            content = self.fetcher.fetch(url, timeout, force_refresh)
            if content is None:
                return False
            self.storage.save_cleaned_and_compressed_data(url, content)
            return True
        except Exception:
            return False

    def get_archived_feed(self, url: str):
        try:
            return self.storage.get_cleaned_and_compressed_data(url)
        except Exception:
            return None


def archive_resilient_clean_rss_flow(
    url: str,
    timeout: int = 10,
    db_path=None,
    max_memory_mb: int = 128,
    force_refresh: bool = False
) -> bool:
    archiver = ResilientCleanRSSArchiver(db_path=db_path, max_memory_mb=max_memory_mb)
    return archiver.archive_feed(url, timeout=timeout, force_refresh=force_refresh)


def resilient_clean_rss_archive_flow(
    url: str,
    timeout: int = 10,
    db_path=None,
    max_memory_mb: int = 128,
    force_refresh: bool = False
):
    archiver = ResilientCleanRSSArchiver(db_path=db_path, max_memory_mb=max_memory_mb)
    return archiver.archive_feed(url, timeout=timeout, force_refresh=force_refresh)
