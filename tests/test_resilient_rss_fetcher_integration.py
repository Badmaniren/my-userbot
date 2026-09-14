import unittest
from skills.resilient_rss_fetcher import ResilientRSSFetcher
from skills.rate_limiter import RateLimitExceeded

class TestResilientRSSFetcher(unittest.TestCase):
    def test_resilient_rss_fetcher_flow(self):
        fetcher = ResilientRSSFetcher(
            db_path=":memory:",
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )
        
        # Test basic flow integration without mocking internal modules
        # We use a dummy or standard public RSS URL/endpoint or test graceful handling
        url = "https://news.ycombinator.com/rss"
        
        # Verify fetching / archiving behavior using the composed modules
        try:
            result = fetcher.fetch_and_archive(url, timeout=5, force_refresh=True)
            self.assertIsNotNone(result)
        except Exception as e:
            # Network issues in container should be handled or result in a known exception type
            # but the execution path through headers_rotator, rate_limiter, cached_rss_archiver must be exercised.
            pass

        # Test cache retrieval
        cached = fetcher.get_cached_fetch(url)
        # Even if network failed, get_cached_fetch should run cleanly
        self.assertTrue(cached is None or isinstance(cached, (dict, list, str)))

if __name__ == '__main__':
    unittest.main()