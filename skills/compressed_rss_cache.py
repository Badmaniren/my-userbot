import json
from skills.payload_compressor import PayloadCompressor, CompressionError
from skills.file_cache import FileCache


class CompressedRSSCacheError(Exception):
    """Исключение для ошибок модуля CompressedRSSCache."""
    pass


class CompressedRSSCache:
    """Кэш для RSS-данных с использованием компрессии и файлового кэша."""

    def __init__(self, cache_dir: str = "rss_cache", default_ttl: int = 300, compression_level: int = 6):
        self.file_cache = FileCache(cache_dir=cache_dir, default_ttl=default_ttl)
        self.compressor = PayloadCompressor(compression_level=compression_level)

    def set_feed(self, url: str, payload: str, ttl: int = None) -> None:
        if not url or not isinstance(url, str):
            raise CompressedRSSCacheError("Invalid URL type or value")
        try:
            compressed_data = self.compressor.compress_text(payload)
            self.file_cache.set(url, compressed_data, ttl=ttl)
        except (CompressionError, OSError) as e:
            raise CompressedRSSCacheError(f"Failed to set feed: {e}") from e
        except Exception as e:
            raise CompressedRSSCacheError(f"Unexpected error in set_feed: {e}") from e

    def get_feed(self, url: str) -> str:
        if not url or not isinstance(url, str):
            return None
        try:
            compressed_data = self.file_cache.get(url)
            if compressed_data is None:
                return None
            return self.compressor.decompress_text(compressed_data)
        except (OSError,) as e:
            raise CompressedRSSCacheError(f"File cache error on get: {e}") from e
        except Exception as e:
            raise CompressedRSSCacheError(f"Decompression or cache error: {e}") from e

    def set_compressed_feed(self, url: str, feed_data, ttl: int = None) -> None:
        try:
            if isinstance(feed_data, (dict, list)):
                payload = json.dumps(feed_data, ensure_ascii=False)
            else:
                payload = str(feed_data)
            self.set_feed(url, payload, ttl=ttl)
        except CompressedRSSCacheError:
            raise
        except Exception as e:
            raise CompressedRSSCacheError(f"Failed to set compressed feed: {e}") from e

    def get_compressed_feed(self, url: str):
        try:
            payload = self.get_feed(url)
            if payload is None:
                return None
            try:
                return json.loads(payload)
            except (json.JSONDecodeError, TypeError):
                return payload
        except CompressedRSSCacheError:
            raise
        except Exception as e:
            raise CompressedRSSCacheError(f"Failed to get compressed feed: {e}") from e


def compress_and_cache_feed(url: str, payload: str, ttl: int = None, cache_dir: str = "rss_cache") -> None:
    cache = CompressedRSSCache(cache_dir=cache_dir)
    cache.set_feed(url, payload, ttl=ttl)


def get_decompressed_cached_feed(url: str, cache_dir: str = "rss_cache") -> str:
    cache = CompressedRSSCache(cache_dir=cache_dir)
    return cache.get_feed(url)