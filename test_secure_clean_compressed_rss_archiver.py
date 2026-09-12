import unittest
from unittest.mock import patch, MagicMock
from skills.secure_clean_compressed_rss_archiver import (
    SecureCleanCompressedRSSArchiver,
    SecureCleanCompressedRSSArchiverError,
    secure_clean_compressed_rss_archive_flow
)

class TestSecureCleanCompressedRSSArchiver(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 60
        self.raise_on_limit = True
        self.test_url = "https://example.com/rss?utm_source=test"
        self.cleaned_url = "https://example.com/rss"

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_init_default(self, mock_resilient_cls, mock_storage_cls):
        archiver = SecureCleanCompressedRSSArchiver()
        self.assertEqual(archiver.db_path, ":memory:")
        self.assertEqual(archiver.max_memory_mb, 512)
        mock_storage_cls.assert_called_once()
        mock_resilient_cls.assert_called_once()

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_init_custom_params(self, mock_resilient_cls, mock_storage_cls):
        archiver = SecureCleanCompressedRSSArchiver(
            db_path="custom.db",
            max_memory_mb=256,
            calls=5,
            period=30,
            raise_on_limit=False
        )
        self.assertEqual(archiver.db_path, "custom.db")
        self.assertEqual(archiver.max_memory_mb, 256)
        self.assertEqual(archiver.calls, 5)
        self.assertEqual(archiver.period, 30)
        self.assertFalse(archiver.raise_on_limit)
        mock_storage_cls.assert_called_once_with(db_path="custom.db")

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_archive_feed_success(self, mock_resilient_cls, mock_storage_cls):
        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = self.cleaned_url

        mock_resilient_instance = mock_resilient_cls.return_value
        mock_resilient_instance.archive_feed.return_value = True

        archiver = SecureCleanCompressedRSSArchiver(db_path=self.db_path)
        result = archiver.archive_feed(self.test_url, timeout=10, force_refresh=True)

        self.assertTrue(result)
        mock_storage_instance.clean_target_url.assert_called_once_with(self.test_url)
        mock_resilient_instance.archive_feed.assert_called_once_with(
            url=self.cleaned_url,
            timeout=10,
            force_refresh=True
        )

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_archive_feed_exception_wrapping(self, mock_resilient_cls, mock_storage_cls):
        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.side_effect = Exception("Storage error")

        archiver = SecureCleanCompressedRSSArchiver(db_path=self.db_path)
        with self.assertRaises(SecureCleanCompressedRSSArchiverError):
            archiver.archive_feed(self.test_url)

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_archive_feed_already_custom_exception(self, mock_resilient_cls, mock_storage_cls):
        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.side_effect = SecureCleanCompressedRSSArchiverError("Custom error")

        archiver = SecureCleanCompressedRSSArchiver(db_path=self.db_path)
        with self.assertRaises(SecureCleanCompressedRSSArchiverError):
            archiver.archive_feed(self.test_url)

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_get_archived_feed_success(self, mock_resilient_cls, mock_storage_cls):
        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = self.cleaned_url
        mock_storage_instance.get_cleaned_and_compressed_data.return_value = b"compressed_data"

        archiver = SecureCleanCompressedRSSArchiver(db_path=self.db_path)
        data = archiver.get_archived_feed(self.test_url)

        self.assertEqual(data, b"compressed_data")
        mock_storage_instance.clean_target_url.assert_called_once_with(self.test_url)
        mock_storage_instance.get_cleaned_and_compressed_data.assert_called_once_with(self.cleaned_url)

    @patch('skills.secure_clean_compressed_rss_archiver.CleanCompressedDBStorage')
    @patch('skills.secure_clean_compressed_rss_archiver.ResilientCleanRSSArchiver')
    def test_get_archived_feed_exception_wrapping(self, mock_resilient_cls, mock_storage_cls):
        mock_storage_instance = mock_storage_cls.return_value
        mock_storage_instance.clean_target_url.return_value = self.cleaned_url
        mock_storage_instance.get_cleaned_and_compressed_data.side_effect = Exception("DB fetch error")

        archiver = SecureCleanCompressedRSSArchiver(db_path=self.db_path)
        with self.assertRaises(SecureCleanCompressedRSSArchiverError):
            archiver.get_archived_feed(self.test_url)

    @patch('skills.secure_clean_compressed_rss_archiver.SecureCleanCompressedRSSArchiver')
    def test_secure_clean_compressed_rss_archive_flow(self, mock_archiver_cls):
        mock_instance = mock_archiver_cls.return_value
        mock_instance.archive_feed.return_value = True

        result = secure_clean_compressed_rss_archive_flow(
            url=self.test_url,
            timeout=5,
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            force_refresh=False,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        self.assertTrue(result)
        mock_archiver_cls.assert_called_once_with(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        mock_instance.archive_feed.assert_called_once_with(
            url=self.test_url,
            timeout=5,
            force_refresh=False
        )

if __name__ == '__main__':
    unittest.main()