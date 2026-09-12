import unittest
from unittest.mock import patch, MagicMock
import io
from skills.resilient_secure_clean_compressed_rss_archiver import (
    ResilientSecureCleanCompressedRSSArchiver,
    SecureCleanCompressedRSSArchiverError,
    secure_clean_compressed_rss_archive_flow
)


class TestResilientSecureCleanCompressedRSSArchiver(unittest.TestCase):

    def test_archive_feed_success(self):
        with patch('skills.resilient_secure_clean_compressed_rss_archiver.ResilientRSSFetcher') as mock_fetcher_cls, \
             patch('skills.resilient_secure_clean_compressed_rss_archiver.BaseArchiver') as mock_base_cls:
            
            mock_fetcher = mock_fetcher_cls.return_value
            mock_fetcher.fetch.return_value = "<rss><channel><title>Test</title></channel></rss>"
            
            mock_base = mock_base_cls.return_value
            mock_base.archive_feed.return_value = True

            archiver = ResilientSecureCleanCompressedRSSArchiver()
            result = archiver.archive_feed("http://example.com/rss")
            self.assertTrue(result)

    def test_archive_feed_fetch_none(self):
        with patch('skills.resilient_secure_clean_compressed_rss_archiver.ResilientRSSFetcher') as mock_fetcher_cls, \
             patch('skills.resilient_secure_clean_compressed_rss_archiver.BaseArchiver') as mock_base_cls:
            
            mock_fetcher = mock_fetcher_cls.return_value
            mock_fetcher.fetch.return_value = None

            archiver = ResilientSecureCleanCompressedRSSArchiver()
            result = archiver.archive_feed("http://example.com/rss")
            self.assertFalse(result)

    def test_archive_feed_exception_raise_on_limit(self):
        with patch('skills.resilient_secure_clean_compressed_rss_archiver.ResilientRSSFetcher') as mock_fetcher_cls:
            mock_fetcher = mock_fetcher_cls.return_value
            mock_fetcher.fetch.side_effect = Exception("Fetch error")

            archiver = ResilientSecureCleanCompressedRSSArchiver(raise_on_limit=True)
            with self.assertRaises(SecureCleanCompressedRSSArchiverError):
                archiver.archive_feed("http://example.com/rss")

    def test_archive_feed_exception_no_raise(self):
        with patch('skills.resilient_secure_clean_compressed_rss_archiver.ResilientRSSFetcher') as mock_fetcher_cls:
            mock_fetcher = mock_fetcher_cls.return_value
            mock_fetcher.fetch.side_effect = Exception("Fetch error")

            archiver = ResilientSecureCleanCompressedRSSArchiver(raise_on_limit=False)
            result = archiver.archive_feed("http://example.com/rss")
            self.assertFalse(result)

    def test_get_archived_feed(self):
        with patch('skills.resilient_secure_clean_compressed_rss_archiver.BaseArchiver') as mock_base_cls:
            mock_base = mock_base_cls.return_value
            mock_base.get_archived_feed.return_value = "cached_data"

            archiver = ResilientSecureCleanCompressedRSSArchiver()
            data = archiver.get_archived_feed("http://example.com/rss")
            self.assertEqual(data, "cached_data")

    def test_secure_clean_compressed_rss_archive_flow(self):
        with patch('skills.resilient_secure_clean_compressed_rss_archiver.ResilientRSSFetcher') as mock_fetcher_cls, \
             patch('skills.resilient_secure_clean_compressed_rss_archiver.BaseArchiver') as mock_base_cls:
            
            mock_fetcher = mock_fetcher_cls.return_value
            mock_fetcher.fetch.return_value = "<rss><channel></channel></rss>"
            
            mock_base = mock_base_cls.return_value
            mock_base.archive_feed.return_value = True

            result = secure_clean_compressed_rss_archive_flow("http://example.com/rss")
            self.assertTrue(result)


if __name__ == "__main__":
    unittest.main()