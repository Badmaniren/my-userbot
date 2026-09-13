import unittest
from skills.clean_url_crawler import clean_url_crawler_flow

class TestCleanUrlCrawlerIntegration(unittest.TestCase):
    def test_clean_url_crawler_composition(self):
        raw_html = '<html><body><a href="https://example.com/path?utm_source=test&ref=123#anchor">Link</a></body></html>'
        base_url = "https://example.com"
        
        result = clean_url_crawler_flow(raw_html, base_url, timeout=5)
        
        self.assertIsInstance(result, list)
        if result:
            self.assertIsInstance(result[0], str)
            self.assertNotIn("utm_source", result[0])

if __name__ == "__main__":
    unittest.main()