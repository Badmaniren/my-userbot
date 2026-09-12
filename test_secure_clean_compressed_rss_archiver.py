import unittest
from unittest.mock import patch, MagicMock
import io

from skills.secure_clean_compressed_rss_archiver import (
    SecureCleanCompressedRSSArchiver,
    SecureCleanCompressedRSSArchiverError,
    secure_clean_compressed_rss_archive_flow
)

class TestSecureCleanCompressedRSSArchiver(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.url = "https://example.com/rss?utm_source=test"
        self.timeout = 5

    def test_init_and_attributes(self):
        archiver = SecureCleanCompressedRSSArchiver(self.db_path, self.max_memory_mb)
        self.assertEqual(archiver.db_path, self.db_path)
        self.assertEqual(archiver.max_memory_mb, self.max_memory_mb)

    @patch("skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver")
    @patch("skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage")
    def test_archive_feed_success(self, mock_storage_cls, mock_resilient_cls):
        mock_resilient_instance = mock_resilient_cls.return_value
        mock_resilient_instance.archive_feed.return_value = True

        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = "https://example.com/rss"
        mock_storage_instance.get_cleaned_and_compressed_data.return_value = b"compressed_payload"

        archiver = SecureCleanCompressedRSSArchiver(self.db_path, self.max_memory_mb)
        result = archiver.archive_feed(self.url, self.timeout, force_refresh=True)

        self.assertTrue(result)
        mock_storage_instance.clean_target_url.assert_called_once_with(self.url)
        mock_resilient_instance.archive_feed.assert_called_once()

    @patch("skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver")
    @patch("skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage")
    def test_archive_feed_failure(self, mock_storage_cls, mock_resilient_cls):
        mock_resilient_instance = mock_resilient_cls.return_value
        mock_resilient_instance.archive_feed.return_value = False

        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = "https://example.com/rss"

        archiver = SecureCleanCompressedRSSArchiver(self.db_path, self.max_memory_mb)
        result = archiver.archive_feed(self.url, self.timeout, force_refresh=False)

        self.assertFalse(result)

    @patch("skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver")
    @patch("skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage")
    def test_archive_feed_exception_handling(self, mock_storage_cls, mock_resilient_cls):
        mock_resilient_instance = mock_resilient_cls.return_value
        mock_resilient_instance.archive_feed.side_effect = Exception("Critical error")

        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = "https://example.com/rss"

        archiver = SecureCleanCompressedRSSArchiver(self.db_path, self.max_memory_mb)
        
        with self.assertRaises(SecureCleanCompressedRSSArchiverError):
            archiver.archive_feed(self.url, self.timeout)

    @patch("skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage")
    def test_get_archived_feed(self, mock_storage_cls):
        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = "https://example.com/rss"
        mock_storage_instance.get_cleaned_and_compressed_data.return_value = b"data"

        archiver = SecureCleanCompressedRSSArchiver(self.db_path, self.max_memory_mb)
        data = archiver.get_archived_feed(self.url)

        self.assertEqual(data, b"data")
        mock_storage_instance.clean_target_url.assert_called_once_with(self.url)
        mock_storage_instance.get_cleaned_and_compressed_data.assert_called_once_with("https://example.com/rss")

    @patch("skills.secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver")
    def test_secure_clean_compressed_rss_archive_flow(self, mock_archiver_cls):
        mock_archiver_instance = mock_archiver_cls.return_value
        mock_archiver_instance.archive_feed.return_value = True

        result = secure_clean_compressed_rss_archive_flow(
            url=self.url,
            timeout=self.timeout,
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            force_refresh=True
        )

        self.assertTrue(result)
        mock_archiver_cls.assert_called_once_with(db_path=self.db_path, max_memory_mb=self.max_memory_mb)
        mock_archiver_instance.archive_feed.assert_called_once_with(
            url=self.url,
            timeout=self.timeout,
            force_refresh=True
        )

if __name__ == "__main__":
    unittest.main()