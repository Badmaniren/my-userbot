import unittest
from unittest.mock import patch, MagicMock
import io
import tempfile
import os

from skills.resilient_clean_rss_archiver import (
    ResilientCleanRSSArchiver,
    ResilientCleanRSSArchiverError,
    archive_resilient_clean_rss_flow
)

class TestResilientCleanRSSArchiver(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(delete=False)
        self.temp_db.close()
        self.db_path = self.temp_db.name
        self.url = "https://example.com/rss.xml"
        self.timeout = 5
        self.max_memory_mb = 128

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.unlink(self.db_path)

    def test_init_and_attributes(self):
        archiver = ResilientCleanRSSArchiver(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=10,
            period=60,
            raise_on_limit=False
        )
        self.assertEqual(archiver.db_path, self.db_path)
        self.assertEqual(archiver.max_memory_mb, self.max_memory_mb)
        self.assertIsNotNone(archiver.storage)
        self.assertIsNotNone(archiver.fetcher)

    def test_archive_feed_success(self):
        archiver = ResilientCleanRSSArchiver(db_path=self.db_path)
        mock_rss_content = b"<rss><channel><title>Test Feed</title></channel></rss>"
        
        with patch('skills.resilient_rss_fetcher.ResilientRSSFetcher.fetch') as mock_fetch, \
             patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.save_cleaned_and_compressed_data') as mock_save:
            
            mock_fetch.return_value = mock_rss_content
            
            result = archiver.archive_feed(self.url, timeout=self.timeout, force_refresh=True)
            
            self.assertTrue(result)
            mock_fetch.assert_called_once_with(self.url, self.timeout, True)
            mock_save.assert_called_once()

    def test_archive_feed_failure(self):
        archiver = ResilientCleanRSSArchiver(db_path=self.db_path)
        
        with patch('skills.resilient_rss_fetcher.ResilientRSSFetcher.fetch') as mock_fetch:
            mock_fetch.side_effect = Exception("Fetch failed")
            
            result = archiver.archive_feed(self.url, timeout=self.timeout)
            
            self.assertFalse(result)

    def test_get_archived_feed_success(self):
        archiver = ResilientCleanRSSArchiver(db_path=self.db_path)
        expected_payload = "<rss><channel><title>Cached Feed</title></channel></rss>"
        
        with patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.get_cleaned_and_compressed_data') as mock_get:
            mock_get.return_value = expected_payload
            
            data = archiver.get_archived_feed(self.url)
            
            self.assertEqual(data, expected_payload)
            mock_get.assert_called_once()

    def test_get_archived_feed_not_found(self):
        archiver = ResilientCleanRSSArchiver(db_path=self.db_path)
        
        with patch('skills.clean_compressed_db_storage.CleanCompressedDBStorage.get_cleaned_and_compressed_data') as mock_get:
            mock_get.return_value = None
            
            data = archiver.get_archived_feed(self.url)
            
            self.assertIsNone(data)

    def test_module_level_archive_flow(self):
        with patch('skills.resilient_clean_rss_archiver.ResilientCleanRSSArchiver.archive_feed') as mock_archive:
            mock_archive.return_value = True
            
            result = archive_resilient_clean_rss_flow(
                url=self.url,
                timeout=self.timeout,
                db_path=self.db_path,
                max_memory_mb=self.max_memory_mb,
                force_refresh=False
            )
            
            self.assertTrue(result)
            mock_archive.assert_called_once()

if __name__ == '__main__':
    unittest.main()