import unittest
import os
import shutil
import tempfile
from skills.compressed_rss_cache import CompressedRSSCache
from skills.payload_compressor import PayloadCompressor
from skills.file_cache import FileCache

class TestCompressedRSSCacheIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.cache = CompressedRSSCache(cache_dir=self.test_dir, default_ttl=60)

    def tearDown(self):
        shutil.rmtree(self.test_dir, ignore_errors=True)

    def test_cache_composition_and_compression(self):
        # Проверяем, что используются реальные классы композиции
        self.assertIsInstance(self.cache.file_cache, FileCache)
        self.assertIsInstance(self.cache.compressor, PayloadCompressor)

        feed_data = [
            {"title": "Test RSS Item 1", "link": "http://example.com/1", "summary": "Some summary text 1"},
            {"title": "Test RSS Item 2", "link": "http://example.com/2", "summary": "Some summary text 2"}
        ]
        url = "http://example.com/rss.xml"

        # Сохранение в кэш с компрессией
        self.cache.set_compressed_feed(url, feed_data)

        # Проверка получения и декомпрессии
        retrieved_data = self.cache.get_compressed_feed(url)
        self.assertEqual(retrieved_data, feed_data)

    def test_cache_miss(self):
        retrieved_data = self.cache.get_compressed_feed("http://example.com/missing.xml")
        self.assertIsNone(retrieved_data)

    def test_direct_storage_and_custom_compression(self):
        # Тестирование прямого метода обертки через payload_compressor и file_cache
        custom_payload = {"status": "ok", "items_count": 42}
        key = "custom_key_xyz"
        
        self.cache.set_compressed_feed(key, custom_payload)
        res = self.cache.get_compressed_feed(key)
        self.assertEqual(res, custom_payload)

if __name__ == "__main__":
    unittest.main()