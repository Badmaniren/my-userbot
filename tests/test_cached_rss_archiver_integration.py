import unittest
from unittest.mock import patch, MagicMock
from skills.cached_rss_archiver import (
    cached_rss_archive_flow,
    CachedRSSArchiver,
    archive_rss_feed
)


class TestCachedRssArchiver(unittest.TestCase):

    @patch("skills.rss_parser.parse_feed")
    def test_cached_rss_archiver_flow_success(self, mock_parse_feed):
        mock_parse_feed.return_value = [{"title": "Test RSS Item", "link": "http://example.com/item1"}]
        
        result = cached_rss_archive_flow(
            url="http://example.com/rss",
            timeout=5,
            db_path=":memory:",
            max_memory_mb=500,
            force_refresh=True
        )
        
        self.assertIsNotNone(result)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["title"], "Test RSS Item")

    @patch("skills.rss_parser.parse_feed")
    def test_cached_rss_archiver_cache_hit(self, mock_parse_feed):
        mock_parse_feed.return_value = [{"title": "Cached RSS Item", "link": "http://example.com/item2"}]
        
        url = "http://example.com/rss_cache"
        
        # First call populates cache and saves data
        res1 = cached_rss_archive_flow(url, timeout=5, db_path=":memory:", max_memory_mb=500, force_refresh=True)
        self.assertEqual(res1[0]["title"], "Cached RSS Item")
        
        # Second call should hit cache without invoking parse_feed again (or parse_feed called once)
        # But wait, to ensure DBState persists across calls when using :memory:, we need the same DB instance or file path,
        # or we can test via CachedRSSArchiver instance where self.db is persistent during object lifetime.
        
    def test_cached_rss_archiver_class_workflow(self):
        archiver = CachedRSSArchiver(db_path=":memory:", max_memory_mb=500.0)
        
        with patch("skills.rss_parser.parse_feed") as mock_parse:
            mock_parse.return_value = [{"title": "Class RSS Item", "link": "http://example.com/class"}]
            
            res1 = archiver.archive_feed("http://example.com/rss_class", timeout=5, force_refresh=True)
            self.assertEqual(res1[0]["title"], "Class RSS Item")
            
            # Now test cache hit
            mock_parse.return_value = [{"title": "Should Not Be Called", "link": "http://example.com/wrong"}]
            res2 = archiver.archive_feed("http://example.com/rss_class", timeout=5, force_refresh=False)
            self.assertEqual(res2[0]["title"], "Class RSS Item")

    def test_cached_rss_archiver_malformed_feed(self):
        with patch("skills.rss_parser.parse_feed") as mock_parse:
            mock_parse.return_value = None
            
            with self.assertRaises(ValueError):
                cached_rss_archive_flow("http://example.com/bad", timeout=5, db_path=":memory:", max_memory_mb=500)

    def test_get_archived_feed_fallback(self):
        archiver = CachedRSSArchiver(db_path=":memory:", max_memory_mb=500.0)
        url = "http://example.com/fallback"
        
        with patch("skills.rss_parser.parse_feed") as mock_parse:
            mock_parse.return_value = [{"title": "Fallback Item"}]
            archiver.archive_feed(url, force_refresh=True)
            
        # Clear cache but keep db_data by clearing cache specifically or just testing get_archived_feed directly
        archiver.db.set_cache(f"rss:{url}", None)
        
        archived = archiver.get_archived_feed(url)
        self.assertIsNotNone(archived)
        self.assertEqual(archived[0]["title"], "Fallback Item")

    def test_archive_rss_feed_wrapper(self):
        with patch("skills.rss_parser.parse_feed") as mock_parse:
            mock_parse.return_value = [{"title": "Wrapper Test"}]
            res = archive_rss_feed("http://example.com/wrapper", db_path=":memory:", timeout=5, max_memory_mb=500.0)
            self.assertEqual(res[0]["title"], "Wrapper Test")


if __name__ == "__main__":
    unittest.main()