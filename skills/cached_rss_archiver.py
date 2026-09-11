import json
from skills import rss_parser
from skills.db_storage import DBStorage
from skills.payload_compressor import PayloadCompressor
from skills.memory_profiler import assert_memory_limit


def cached_rss_archive_flow(url, timeout=5, db_path=":memory:", max_memory_mb=500, force_refresh=False):
    assert_memory_limit(max_memory_mb)

    db = DBStorage(db_path=db_path)
    cache_key = f"rss:{url}"

    if not force_refresh:
        cached_data = db.get_cache(cache_key)
        if cached_data is not None:
            compressor = PayloadCompressor()
            if hasattr(compressor, "decompress_payload"):
                return compressor.decompress_payload(cached_data)
            elif hasattr(compressor, "decompress_json"):
                return compressor.decompress_json(cached_data)

    feed_items = rss_parser.parse_feed(url, timeout=timeout)
    if feed_items is None:
        raise ValueError("Malformed feed data returned None")

    compressor = PayloadCompressor()
    if hasattr(compressor, "compress_payload"):
        compressed_payload = compressor.compress_payload(feed_items)
    else:
        compressed_payload = compressor.compress_json(feed_items)

    db.set_cache(cache_key, compressed_payload)
    db.save_data(cache_key, compressed_payload)

    return feed_items


class CachedRSSArchiver:
    def __init__(self, db_path=":memory:", max_memory_mb=500.0):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.db = DBStorage(db_path=db_path)
        self.compressor = PayloadCompressor()

    def archive_feed(self, url, timeout=5, force_refresh=False):
        assert_memory_limit(self.max_memory_mb)
        cache_key = f"rss:{url}"

        if not force_refresh:
            cached_data = self.db.get_cache(cache_key)
            if cached_data is not None:
                if hasattr(self.compressor, "decompress_payload"):
                    return self.compressor.decompress_payload(cached_data)
                return self.compressor.decompress_json(cached_data)

        feed_items = rss_parser.parse_feed(url, timeout=timeout)
        if feed_items is None:
            raise ValueError("Malformed feed data returned None")

        if hasattr(self.compressor, "compress_payload"):
            compressed_payload = self.compressor.compress_payload(feed_items)
        else:
            compressed_payload = self.compressor.compress_json(feed_items)

        self.db.set_cache(cache_key, compressed_payload)
        self.db.save_data(cache_key, compressed_payload)

        return feed_items

    def get_archived_feed(self, url):
        cache_key = f"rss:{url}"
        cached_data = self.db.get_cache(cache_key)
        if cached_data is None:
            cached_data = self.db.get_data(cache_key)
        if cached_data is not None:
            if hasattr(self.compressor, "decompress_payload"):
                return self.compressor.decompress_payload(cached_data)
            return self.compressor.decompress_json(cached_data)
        return None


def archive_rss_feed(url, db_path=":memory:", timeout=5, max_memory_mb=500.0):
    archiver = CachedRSSArchiver(db_path=db_path, max_memory_mb=max_memory_mb)
    return archiver.archive_feed(url, timeout=timeout)