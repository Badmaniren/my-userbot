import unittest
from unittest.mock import patch, MagicMock
from skills.cached_rss_archiver import (
    cached_rss_archive_flow,
    CachedRSSArchiver,
    archive_rss_feed
)
from skills.payload_compressor import PayloadCompressor
from skills.memory_profiler import MemoryLimitExceeded


class TestCachedRssArchiver(unittest.TestCase):

    def setUp(self):
        self.sample_feed = [
            {"title": "Test Item 1", "link": "http://example.com/1"},
            {"title": "Test Item 2", "link": "http://example.com/2"}
        ]
        self.compressor = PayloadCompressor()

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_cached_rss_archiver_flow_success(self, mock_parse_feed):
        mock_parse_feed.return_value = self.sample_feed
        result = cached_rss_archive_flow("http://example.com/rss", timeout=5, db_path=":memory:", max_memory_mb=500, force_refresh=True)
        self.assertEqual(result, self.sample_feed)

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_cached_rss_archiver_flow_malformed_feed(self, mock_parse_feed):
        mock_parse_feed.return_value = None
        with self.assertRaises(ValueError):
            cached_rss_archive_flow("http://example.com/bad_rss", timeout=5, db_path=":memory:", max_memory_mb=500, force_refresh=True)

    @patch("skills.cached_rss_archiver.assert_memory_limit")
    def test_cached_rss_archiver_memory_exceeded(self, mock_assert_memory):
        mock_assert_memory.side_effect = MemoryLimitExceeded("Out of memory")
        with self.assertRaises(MemoryLimitExceeded):
            cached_rss_archive_flow("http://example.com/rss", max_memory_mb=1)

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_cached_rss_archiver_cache_hit(self, mock_parse_feed):
        url = "http://example.com/cache_test"
        compressed = self.compressor.compress_payload(self.sample_feed)
        
        with patch("skills.cached_rss_archiver.DBStorage") as MockDB:
            instance = MockDB.return_value
            instance.get_cache.return_value = compressed
            
            result = cached_rss_archive_flow(url, force_refresh=False)
            self.assertEqual(result, self.sample_feed)
            mock_parse_feed.assert_not_called()

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_cached_rss_archiver_class_workflow(self, mock_parse_feed):
        mock_parse_feed.return_value = self.sample_feed
        archiver = CachedRSSArchiver(db_path=":memory:", max_memory_mb=500)
        
        result = archiver.archive_feed("http://example.com/rss", timeout=3, force_refresh=True)
        self.assertEqual(result, self.sample_feed)

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_cached_rss_archiver_get_archived_feed_found(self, mock_parse_feed):
        url = "http://example.com/archived"
        compressed = self.compressor.compress_payload(self.sample_feed)
        
        archiver = CachedRSSArchiver(db_path=":memory:")
        with patch.object(archiver.db, "get_cache", return_value=None), \
             patch.object(archiver.db, "get_data", return_value=compressed):
            
            result = archiver.get_archived_feed(url)
            self.assertEqual(result, self.sample_feed)

    def test_cached_rss_archiver_get_archived_feed_not_found(self):
        archiver = CachedRSSArchiver(db_path=":memory:")
        with patch.object(archiver.db, "get_cache", return_value=None), \
             patch.object(archiver.db, "get_data", return_value=None):
            
            result = archiver.get_archived_feed("http://example.com/missing")
            self.assertIsNone(result)

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_archive_rss_feed_helper(self, mock_parse_feed):
        mock_parse_feed.return_value = self.sample_feed
        result = archive_rss_feed("http://example.com/rss", db_path=":memory:", timeout=5, max_memory_mb=500.0)
        self.assertEqual(result, self.sample_feed)

    @patch("skills.cached_rss_archiver.rss_parser.parse_feed")
    def test_cached_rss_archiver_decompression_failure(self, mock_parse_feed):
        url = "http://example.com/corrupt_cache"
        with patch("skills.cached_rss_archiver.DBStorage") as MockDB:
            instance = MockDB.return_value
            instance.get_cache.return_value = "invalid_compressed_data"
            
            with patch.object(PayloadCompressor, "decompress_payload", side_effect=Exception("Decompression failed")):
                with self.assertRaises(Exception):
                    cached_rss_archive_flow(url, force_refresh=False)


if __name__ == "__main__":
    unittest.main()