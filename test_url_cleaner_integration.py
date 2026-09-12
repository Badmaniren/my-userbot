import unittest
from skills.url_cleaner import clean_url, normalize_url
from skills.query_string_parser import QueryStringParser, normalize_query

class TestURLCleanerIntegration(unittest.TestCase):
    def test_url_cleaning_and_normalization_flow(self):
        dirty_url = "https://example.com/path?utm_source=google&utm_medium=cpc&id=123&utm_campaign=test#anchor"
        
        cleaned = clean_url(dirty_url)
        self.assertIsInstance(cleaned, str)
        self.assertNotIn("utm_source", cleaned)
        self.assertNotIn("utm_medium", cleaned)
        self.assertNotIn("utm_campaign", cleaned)
        self.assertIn("id=123", cleaned)

        normalized = normalize_url(cleaned)
        self.assertIsInstance(normalized, str)
        
        parser = QueryStringParser(normalized)
        self.assertEqual(parser.get("id"), "123")
        
        query_normalized = normalize_query(dirty_url, remove_empty=True, deduplicate=True)
        self.assertIsInstance(query_normalized, str)

if __name__ == "__main__":
    unittest.main()