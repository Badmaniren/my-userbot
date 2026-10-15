import unittest
from unittest.mock import patch, MagicMock
from skills.resilient_rss_fetcher import (
    ResilientRSSFetcher,
    ResilientFetcherError
)
from skills.rate_limiter import RateLimitExceeded
from skills.db_storage import DBStorage
from skills.headers_rotator import HeadersRotator
from skills.cached_rss_archiver import CachedRSSArchiver


class TestResilientRSSFetcher(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.url = "https://example.com/rss.xml"
        self.timeout = 5

    def test_init_components(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path, calls=5, period=1.0)
        self.assertIsInstance(fetcher.db, DBStorage)
        self.assertIsInstance(fetcher.headers_rotator, HeadersRotator)
        self.assertIsInstance(fetcher.archiver, CachedRSSArchiver)

    def test_fetch_success(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)
        mock_data = {"feed": "valid_rss_content", "items": []}

        with patch.object(fetcher.rate_limiter, 'acquire') as mock_acquire, \
             patch.object(fetcher.headers_rotator, 'rotate_headers') as mock_rotate, \
             patch.object(fetcher.archiver, 'archive_feed', return_value=mock_data) as mock_archive:
            
            result = fetcher.fetch(self.url, timeout=self.timeout)
            
            self.assertTrue(mock_acquire.called)
            self.assertTrue(mock_rotate.called)
            mock_archive.assert_called_once_with(self.url, self.timeout, force_refresh=False)
            self.assertEqual(result, mock_data)

    def test_fetch_rate_limit_exceeded(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)

        with patch.object(fetcher.rate_limiter, 'acquire', side_effect=RateLimitExceeded("Limit reached")) as mock_acquire:
            with self.assertRaises((RateLimitExceeded, ResilientFetcherError)):
                fetcher.fetch(self.url, timeout=self.timeout)

    def test_fetch_archiver_failure_raises_resilient_error(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)

        with patch.object(fetcher.rate_limiter, 'acquire'), \
             patch.object(fetcher.headers_rotator, 'rotate_headers'), \
             patch.object(fetcher.archiver, 'archive_feed', side_effect=Exception("Network error")):
            
            with self.assertRaises(ResilientFetcherError):
                fetcher.fetch(self.url, timeout=self.timeout)

    def test_fetch_with_force_refresh(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)
        mock_data = {"feed": "refreshed_content"}

        with patch.object(fetcher.rate_limiter, 'acquire'), \
             patch.object(fetcher.headers_rotator, 'rotate_headers'), \
             patch.object(fetcher.archiver, 'archive_feed', return_value=mock_data) as mock_archive:
            
            result = fetcher.fetch(self.url, timeout=self.timeout, force_refresh=True)
            mock_archive.assert_called_once_with(self.url, self.timeout, force_refresh=True)
            self.assertEqual(result, mock_data)

    def test_get_cached_feed_fallback(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)
        mock_data = {"feed": "cached_content"}

        with patch.object(fetcher.archiver, 'get_archived_feed', return_value=mock_data) as mock_get:
            result = fetcher.get_cached(self.url)
            mock_get.assert_called_once_with(self.url)
            self.assertEqual(result, mock_data)

    def test_get_cached_feed_missing(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)

        with patch.object(fetcher.archiver, 'get_archived_feed', return_value=None) as mock_get:
            result = fetcher.get_cached(self.url)
            mock_get.assert_called_once_with(self.url)
            self.assertIsNone(result)

    def test_header_validation_failure_handling(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)

        with patch.object(fetcher.rate_limiter, 'acquire'), \
             patch.object(fetcher.headers_rotator, 'rotate_headers'), \
             patch.object(fetcher.headers_rotator, 'validate_headers_against_target', return_value=False):
            
            with self.assertRaises(ResilientFetcherError):
                fetcher.fetch(self.url, timeout=self.timeout)

    def test_empty_url_handling(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)

        with self.assertRaises((ValueError, ResilientFetcherError, Exception)):
            fetcher.fetch("", timeout=self.timeout)

    def test_invalid_timeout_handling(self):
        fetcher = ResilientRSSFetcher(db_path=self.db_path)

        with self.assertRaises((ValueError, TypeError, Exception)):
            fetcher.fetch(self.url, timeout=-1)


if __name__ == "__main__":
    unittest.main()