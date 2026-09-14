from skills.cached_rss_archiver import CachedRSSArchiver


class ResilientCleanRSSArchiver(CachedRSSArchiver):
    def archive_feed(self, url, timeout=5, force_refresh=False):
        try:
            return super().archive_feed(url, timeout=timeout, force_refresh=force_refresh)
        except Exception:
            return False
