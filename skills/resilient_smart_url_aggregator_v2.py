import requests
from skills import (
    resilient_secure_clean_url_crawler_v2,
    smart_secure_compressed_sitemap_crawler_v2,
    compressed_db_storage,
    memory_profiler
)

class ResilientSmartUrlAggregatorV2:
    def __init__(self, db_path=None, crawler=None, sitemap_crawler=None, storage=None):
        self.db_path = db_path
        self.crawler = crawler or resilient_secure_clean_url_crawler_v2.ResilientSecureCleanUrlCrawlerV2()

        self.sitemap_crawler = sitemap_crawler or smart_secure_compressed_sitemap_crawler_v2.SmartSecureCompressedSitemapCrawlerV2(
            db_path=db_path,
            max_memory_mb=128,
            calls=10,
            period=60
        )
        self.storage = storage or compressed_db_storage.CompressedDBStorage(db_path=db_path)

    def aggregate(self, url, timeout=10):
        try:
            if not self.crawler.process_url(url, timeout=timeout):
                return False

            sitemap_data = self.sitemap_crawler.crawl_and_clean(url, timeout=timeout)
            if sitemap_data is not None:
                self.storage.save_compressed_data(url, str(sitemap_data).encode())
                return True
            return False
        except Exception:
            return False

    def save_to_storage(self, key, data):
        result = self.storage.save_compressed_data(key, data)
        if result is False:
            raise Exception("DB Error")
        return result

    def validate_source(self, url, timeout=10):
        try:
            result = self.sitemap_crawler.validate_sitemap(url, timeout=timeout)
            return bool(result)
        except Exception:
            return False

    def validate_target(self, url, timeout=10):
        try:
            result = self.crawler.process_url(url, timeout=timeout)
            return bool(result)
        except Exception:
            return False

    def check_resources(self):
        memory_profiler.assert_memory_limit()

    def get_data(self, key):
        return self.storage.get_compressed_data(key)

    def process_raw_content(self, url):
        try:
            response = requests.get(url, timeout=10)
            return response.status_code == 200
        except requests.RequestException:
            return False

    def get_cached_aggregation(self, url):
        return self.storage.get_compressed_data(url)

    def check_sitemap_health(self, url, timeout=10):
        try:
            return bool(self.sitemap_crawler.validate_sitemap(url, timeout=timeout))
        except Exception:
            return False
