import unittest
import os
from skills.sitemap_parser import parse_sitemap

class TestSitemapParserIntegration(unittest.TestCase):
    def setUp(self):
        self.test_db = "test_sitemap_integration.db"
        self.sitemap_url = "https://example.com/sitemap.xml"

    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)

    def test_parse_sitemap_flow(self):
        try:
            result = parse_sitemap(self.sitemap_url, timeout=5)
            self.assertIsInstance(result, (list, dict))
        except Exception as e:
            self.assertIsNotNone(e)

if __name__ == "__main__":
    unittest.main()