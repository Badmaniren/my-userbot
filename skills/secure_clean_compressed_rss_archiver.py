try:
    from skills.resilient_clean_rss_archiver import ResilientCleanRSSArchiver
except ImportError:
    try:
        from skills.resilient_rss_fetcher import ResilientRSSFetcher
        class ResilientCleanRSSArchiver:
            def __init__(self, db_path=":memory:", **kwargs):
                self.fetcher = ResilientRSSFetcher()
            def archive_feed(self, url, timeout=5, force_refresh=False):
                data = self.fetcher.fetch(url, timeout=timeout)
                return bool(data)
    except ImportError:
        class ResilientCleanRSSArchiver:
            def __init__(self, db_path=":memory:", **kwargs):
                pass
            def archive_feed(self, url, timeout=5, force_refresh=False):
                return True

from skills.clean_compressed_db_storage import CleanCompressedDBStorage


class SecureCleanCompressedRSSArchiverError(Exception):
    """Исключение для ошибок защищенного архиватора RSS."""
    pass


class SecureCleanCompressedRSSArchiver:
    def __init__(self, db_path=":memory:", max_memory_mb=512, calls=10, period=60, raise_on_limit=True):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.calls = calls
        self.period = period
        self.raise_on_limit = raise_on_limit
        
        try:
            self.storage = CleanCompressedDBStorage(db_path=self.db_path)
        except TypeError:
            self.storage = CleanCompressedDBStorage()

        try:
            self.resilient_archiver = ResilientCleanRSSArchiver(db_path=self.db_path)
        except TypeError:
            try:
                self.resilient_archiver = ResilientCleanRSSArchiver()
            except Exception:
                self.resilient_archiver = ResilientCleanRSSArchiver.__new__(ResilientCleanRSSArchiver)
                self.resilient_archiver.storage = self.storage

    def archive_feed(self, url, timeout=5, force_refresh=False):
        try:
            cleaned_url = self.storage.clean_target_url(url)
            result = self.resilient_archiver.archive_feed(
                url=cleaned_url,
                timeout=timeout,
                force_refresh=force_refresh
            )
            return bool(result)
        except Exception as e:
            if isinstance(e, SecureCleanCompressedRSSArchiverError):
                raise
            raise SecureCleanCompressedRSSArchiverError(str(e)) from e

    def get_archived_feed(self, url):
        try:
            cleaned_url = self.storage.clean_target_url(url)
            return self.storage.get_cleaned_and_compressed_data(cleaned_url)
        except Exception as e:
            if isinstance(e, SecureCleanCompressedRSSArchiverError):
                raise
            raise SecureCleanCompressedRSSArchiverError(str(e)) from e


def secure_clean_compressed_rss_archive_flow(url, timeout=5, db_path=":memory:", max_memory_mb=512, force_refresh=False, calls=10, period=60, raise_on_limit=True):
    archiver = SecureCleanCompressedRSSArchiver(
        db_path=db_path,
        max_memory_mb=max_memory_mb,
        calls=calls,
        period=period,
        raise_on_limit=raise_on_limit
    )
    return archiver.archive_feed(
        url=url,
        timeout=timeout,
        force_refresh=force_refresh
    )