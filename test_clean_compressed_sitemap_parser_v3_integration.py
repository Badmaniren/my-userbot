import os
import tempfile
import unittest
from skills.clean_compressed_sitemap_parser_v3 import CleanCompressedSitemapParserV3
from skills.clean_sitemap_parser_v2 import CleanSitemapParserV2
from skills.clean_compressed_db_storage import CleanCompressedDBStorage

class TestCleanCompressedSitemapParserV3Integration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.test_dir.name, "test_sitemap_cache.db")
        self.parser = CleanCompressedSitemapParserV3(db_path=self.db_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_composition_and_parsing_flow(self):
        test_url = "https://example.com/sitemap.xml"
        
        has_base_parser = isinstance(self.parser.sitemap_parser, CleanSitemapParserV2)
        has_storage = isinstance(self.parser.storage, CleanCompressedDBStorage)
        
        self.assertTrue(has_base_parser, "Модуль должен композиционировать CleanSitemapParserV2")
        self.assertTrue(has_storage, "Модуль должен композиционировать CleanCompressedDBStorage")

        cleaned_url = self.parser.storage.clean_target_url(test_url)
        self.assertIsInstance(cleaned_url, str)

        cached_data = self.parser.storage.get_cleaned_and_compressed_data(cleaned_url)
        self.assertIsNone(cached_data)

    def test_cache_and_resilience_integration(self):
        test_url = "https://example.org/sitemap_index.xml"
        cleaned_url = self.parser.storage.clean_target_url(test_url)
        
        dummy_payload = "https://example.org/page1\nhttps://example.org/page2"
        self.parser.storage.save_cleaned_and_compressed_data(cleaned_url, dummy_payload)
        
        retrieved_data = self.parser.storage.get_cleaned_and_compressed_data(cleaned_url)
        self.assertIsNotNone(retrieved_data)

if __name__ == "__main__":
    unittest.main()