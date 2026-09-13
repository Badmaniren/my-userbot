from skills.cached_rss_archiver import CachedRSSArchiver
from skills.clean_compressed_db_storage import CleanCompressedDBStorage


class ResilientCleanRSSArchiverError(Exception):
    """Исключение для ошибок отказоустойчивого архиватора RSS."""
    pass


class ResilientCleanRSSArchiver:
    def __init__(self, db_path=":memory:", max_memory_mb=512):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        try:
            self.storage = CleanCompressedDBStorage(db_path=self.db_path)
        except TypeError:
            self.storage = CleanCompressedDBStorage()

        try:
            self.cached_archiver = CachedRSSArchiver(db_path=self.db_path, max_memory_mb=self.max_memory_mb)
        except TypeError:
            self.cached_archiver = CachedRSSArchiver(db_path=self.db_path)

    def archive_feed(self, url, timeout=5, force_refresh=False):
        try:
            cleaned_url = self.storage.clean_target_url(url)
            feed_items = self.cached_archiver.archive_feed(cleaned_url, timeout=timeout, force_refresh=force_refresh)
            if feed_items is not None:
                self.storage.set_cleaned_compressed_cache(cleaned_url, feed_items)
            return True
        except Exception as e:
            if isinstance(e, ResilientCleanRSSArchiverError):
                raise
            raise ResilientCleanRSSArchiverError(str(e)) from e

    def get_archived_feed(self, url):
        try:
            cleaned_url = self.storage.clean_target_url(url)
            cached_data = self.storage.get_cleaned_and_compressed_data(cleaned_url)
            if cached_data is not None:
                return cached_data
            return self.cached_archiver.get_archived_feed(cleaned_url)
        except Exception as e:
            if isinstance(e, ResilientCleanRSSArchiverError):
                raise
            raise ResilientCleanRSSArchiverError(str(e)) from e


def resilient_clean_rss_archive_flow(url, timeout=5, db_path=":memory:", max_memory_mb=512, force_refresh=False):
    archiver = ResilientCleanRSSArchiver(db_path=db_path, max_memory_mb=max_memory_mb)
    return archiver.archive_feed(url=url, timeout=timeout, force_refresh=force_refresh)


def archive_resilient_clean_rss_flow(url, timeout=5, db_path=":memory:", max_memory_mb=512, force_refresh=False):
    return resilient_clean_rss_archive_flow(
        url=url,
        timeout=timeout,
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        force_refresh=force_refresh
    )
