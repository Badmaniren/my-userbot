from skills.clean_sitemap_parser_v2 import CleanSitemapParserV2, CleanSitemapParserError
from skills.clean_compressed_db_storage import CleanCompressedDBStorage, CleanCompressedDBStorageError


class CleanCompressedSitemapParserError(Exception):
    """Кастомное исключение для CleanCompressedSitemapParserV3."""
    pass


class CleanCompressedSitemapParserV3:
    def __init__(self, db_path=":memory:", max_memory_mb=128):
        self.db_path = db_path
        self.max_memory_mb = max_memory_mb
        self.sitemap_parser = CleanSitemapParserV2()
        self.storage = CleanCompressedDBStorage(db_path=db_path)

    def parse(self, url: str, timeout: int = 10):
        try:
            cleaned_url = self.storage.clean_target_url(url)
        except CleanCompressedDBStorageError:
            cleaned_url = url

        try:
            cached_data = self.storage.get_cleaned_and_compressed_data(cleaned_url)
            if cached_data is not None:
                return cached_data
        except CleanCompressedDBStorageError:
            pass

        try:
            links = self.sitemap_parser.parse(url, timeout)
        except CleanSitemapParserError as e:
            raise CleanCompressedSitemapParserError(f"Failed to parse sitemap: {e}")
        except Exception as e:
            raise CleanCompressedSitemapParserError(f"Failed to parse sitemap: {e}")

        try:
            self.storage.set_cleaned_compressed_cache(cleaned_url, links)
        except CleanCompressedDBStorageError:
            pass

        return links

    def parse_sitemap(self, url: str, timeout: int = 10):
        return self.parse(url, timeout=timeout)

    def parse_and_clean(self, url: str, timeout: int = 10):
        try:
            cleaned_url = self.storage.clean_target_url(url)
        except CleanCompressedDBStorageError:
            cleaned_url = url

        try:
            links = self.sitemap_parser.parse_and_clean(url, timeout)
        except CleanSitemapParserError as e:
            raise CleanCompressedSitemapParserError(f"Failed to parse and clean sitemap: {e}")
        except Exception as e:
            raise CleanCompressedSitemapParserError(f"Failed to parse and clean sitemap: {e}")

        try:
            self.storage.save_cleaned_and_compressed_data(cleaned_url, links)
        except CleanCompressedDBStorageError:
            pass

        return links

    def validate_sitemap(self, url: str, timeout: int = 10) -> bool:
        try:
            result = self.sitemap_parser.validate_sitemap(url, timeout)
            if isinstance(result, tuple):
                return bool(result[0])
            return bool(result)
        except CleanSitemapParserError:
            return False
        except Exception:
            return False
