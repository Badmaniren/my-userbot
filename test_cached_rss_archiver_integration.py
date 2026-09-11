import http.server
import os
import socketserver
import tempfile
import threading
import unittest

from skills.cached_rss_archiver import CachedRSSArchiver, archive_rss_feed
from skills.memory_profiler import MemoryLimitExceeded
from skills.payload_compressor import PayloadCompressor

SAMPLE_RSS_XML = """<?xml version="1.0" encoding="UTF-8" ?>
<rss version="2.0">
<channel>
  <title>Integration Test Feed</title>
  <link>http://localhost</link>
  <description>Integration Feed Description</description>
  <item>
    <title>Post 1</title>
    <link>http://localhost/post/1</link>
    <description>Summary of post 1</description>
  </item>
  <item>
    <title>Post 2</title>
    <link>http://localhost/post/2</link>
    <description>Summary of post 2</description>
  </item>
</channel>
</rss>
"""


class MockFeedHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.server.request_count += 1
        content = SAMPLE_RSS_XML.encode("utf-8")
        self.send_response(200)
        self.send_header("Content-Type", "application/rss+xml; charset=utf-8")
        self.send_header("Content-Length", str(len(content)))
        self.end_headers()
        self.wfile.write(content)

    def log_message(self, format, *args):
        pass


class TestCachedRSSArchiverIntegration(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.httpd = socketserver.TCPServer(("127.0.0.1", 0), MockFeedHandler)
        cls.httpd.request_count = 0
        cls.port = cls.httpd.server_address[1]
        cls.server_thread = threading.Thread(target=cls.httpd.serve_forever, daemon=True)
        cls.server_thread.start()

    @classmethod
    def tearDownClass(cls):
        cls.httpd.shutdown()
        cls.httpd.server_close()
        cls.server_thread.join(timeout=2.0)

    def setUp(self):
        self.feed_url = f"http://127.0.0.1:{self.port}/feed.xml"
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "archiver_test.db")
        self.httpd.request_count = 0

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_archive_feed_and_storage(self):
        archiver = CachedRSSArchiver(db_path=self.db_path, max_memory_mb=1024.0)
        items = archiver.archive_feed(self.feed_url, timeout=5)

        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 2)
        titles = [item.get("title") for item in items]
        self.assertIn("Post 1", titles)
        self.assertIn("Post 2", titles)

        archived = archiver.get_archived_feed(self.feed_url)
        self.assertIsNotNone(archived)
        self.assertEqual(len(archived), 2)
        self.assertEqual(items, archived)

    def test_caching_skips_network(self):
        archiver = CachedRSSArchiver(db_path=self.db_path, max_memory_mb=1024.0)

        first_result = archiver.archive_feed(self.feed_url, timeout=5)
        self.assertEqual(self.httpd.request_count, 1)

        second_result = archiver.archive_feed(self.feed_url, timeout=5, force_refresh=False)
        self.assertEqual(self.httpd.request_count, 1)
        self.assertEqual(first_result, second_result)

    def test_force_refresh_fetches_again(self):
        archiver = CachedRSSArchiver(db_path=self.db_path, max_memory_mb=1024.0)

        archiver.archive_feed(self.feed_url, timeout=5)
        self.assertEqual(self.httpd.request_count, 1)

        archiver.archive_feed(self.feed_url, timeout=5, force_refresh=True)
        self.assertEqual(self.httpd.request_count, 2)

    def test_payload_compression_in_db(self):
        archiver = CachedRSSArchiver(db_path=self.db_path, max_memory_mb=1024.0)
        archiver.archive_feed(self.feed_url, timeout=5)

        cache_key = f"rss:{self.feed_url}"
        raw_cached = archiver.db.get_cache(cache_key)
        if raw_cached is None:
            raw_cached = archiver.db.get_data(cache_key)

        self.assertIsNotNone(raw_cached)
        self.assertIsInstance(raw_cached, str)

        compressor = PayloadCompressor()
        decompressed_items = compressor.decompress_json(raw_cached)
        self.assertIsInstance(decompressed_items, list)
        self.assertEqual(len(decompressed_items), 2)
        self.assertEqual(decompressed_items[0]["title"], "Post 1")

    def test_memory_limit_exceeded(self):
        archiver = CachedRSSArchiver(db_path=self.db_path, max_memory_mb=0.0001)
        with self.assertRaises(MemoryLimitExceeded):
            archiver.archive_feed(self.feed_url, timeout=5)

    def test_archive_rss_feed_convenience_function(self):
        items = archive_rss_feed(
            url=self.feed_url,
            db_path=self.db_path,
            timeout=5,
            max_memory_mb=1024.0
        )
        self.assertIsInstance(items, list)
        self.assertEqual(len(items), 2)
        self.assertEqual(items[0]["title"], "Post 1")


if __name__ == "__main__":
    unittest.main()