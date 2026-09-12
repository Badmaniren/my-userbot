import os
import tempfile
import unittest
from skills.clean_compressed_db_storage import CleanCompressedDBStorage
from skills.url_cleaner import clean_url
from skills.compressed_db_storage import CompressedDBStorage
from skills.clean_text import clean

class TestCleanCompressedDBStorageIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, "test_storage.db")
        self.storage = CleanCompressedDBStorage(self.db_path)

    def tearDown(self):
        self.cleanup_storage()
        self.test_dir.cleanup()

    def cleanup_storage(self):
        if hasattr(self, 'db_path') and os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_clean_and_store_integration(self):
        dirty_url = "https://EXAMPLE.com/path?utm_source=test&param=value"
        dirty_text = "  <p>Hello, <b>World!</b> &amp; Welcome.</p>  "
        
        expected_url = clean_url(dirty_url)
        expected_text = clean(dirty_text)
        
        payload = {
            "url": dirty_url,
            "content": dirty_text
        }
        
        self.storage.save_cleaned_and_compressed_data(expected_url, payload)
        
        retrieved_data = self.storage.get_cleaned_and_compressed_data(expected_url)
        
        self.assertIsNotNone(retrieved_data)
        self.assertEqual(retrieved_data["url"], dirty_url)
        self.assertEqual(clean(retrieved_data["content"]), expected_text)

    def test_cache_integration(self):
        key = "https://example.com/cache-test?utm_campaign=summer"
        clean_key = clean_url(key)
        payload = {"status": "active", "data": "some compressed payload text"}
        
        self.storage.set_cleaned_compressed_cache(clean_key, payload, ttl=60)
        cached_data = self.storage.get_cleaned_compressed_cache(clean_key)
        
        self.assertIsNotNone(cached_data)
        self.assertEqual(cached_data["status"], "active")

if __name__ == "__main__":
    unittest.main()