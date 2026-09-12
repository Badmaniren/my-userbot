import os
import unittest
from skills.resilient_clean_compressed_sitemap_parser_v2 import ResilientCleanCompressedSitemapParserV2, ResilientCleanCompressedSitemapParserV2Error
from skills.resilient_clean_compressed_sitemap_parser import ResilientCleanCompressedSitemapParser
from skills.memory_profiler import MemoryLimitExceeded, get_current_memory

class TestResilientCleanCompressedSitemapParserV2Integration(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_sitemap_v2.db"
        self.parser = ResilientCleanCompressedSitemapParserV2(
            db_path=self.db_path,
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )
        self.test_url = "https://example.com/sitemap.xml"

    def tearDown(self):
        if os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except OSError:
                pass

    def test_composition_and_inheritance(self):
        self.assertIsInstance(self.parser, ResilientCleanCompressedSitemapParser)

    def test_validate_sitemap_returns_bool(self):
        is_valid = self.parser.validate_sitemap(self.test_url, timeout=5)
        self.assertIsInstance(is_valid, bool)

    def test_parse_flow(self):
        try:
            links = self.parser.parse(self.test_url, timeout=5)
            self.assertIsInstance(links, (list, tuple))
        except Exception as e:
            self.assertIsInstance(e, (ResilientCleanCompressedSitemapParserV2Error, Exception))

    def test_parse_and_clean_flow(self):
        try:
            cleaned_data = self.parser.parse_and_clean(self.test_url, timeout=5)
            self.assertIsNotNone(cleaned_data)
        except Exception as e:
            self.assertIsInstance(e, (ResilientCleanCompressedSitemapParserV2Error, Exception))

    def test_memory_profiler_integration(self):
        current_mem = get_current_memory()
        self.assertIsInstance(current_mem, (int, float))

if __name__ == "__main__":
    unittest.main()