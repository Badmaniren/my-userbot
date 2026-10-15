import unittest
from unittest.mock import patch, MagicMock
import io

from skills.url_cleaner import (
    clean_url,
    normalize_url,
    remove_utm_params,
    UrlCleanerError
)


class TestUrlCleaner(unittest.TestCase):

    def test_remove_utm_params_success(self):
        url = "https://example.com/page?utm_source=google&utm_medium=cpc&id=123"
        cleaned = remove_utm_params(url)
        self.assertNotIn("utm_source", cleaned)
        self.assertNotIn("utm_medium", cleaned)
        self.assertIn("id=123", cleaned)

    def test_remove_utm_params_no_params(self):
        url = "https://example.com/page"
        cleaned = remove_utm_params(url)
        self.assertEqual(cleaned, url)

    def test_normalize_url_success(self):
        url = "HTTPS://EXAMPLE.COM/page/?utm_campaign=test#anchor"
        normalized = normalize_url(url)
        self.assertTrue(normalized.startswith("https://example.com"))
        self.assertNotIn("utm_campaign", normalized)
        self.assertNotIn("#anchor", normalized)

    def test_clean_url_success(self):
        url = "http://www.example.com:80/path/../path/file.html?utm_source=twitter"
        cleaned = clean_url(url)
        self.assertTrue(isinstance(cleaned, str))
        self.assertNotIn("utm_source", cleaned)
        self.assertNotIn("www.", cleaned)

    def test_clean_url_invalid_type(self):
        with self.assertRaises((TypeError, UrlCleanerError)):
            clean_url(None)

    def test_clean_url_malformed(self):
        malformed_url = "ht!tp://inv@lid_url"
        result = clean_url(malformed_url)
        self.assertFalse(bool(result) and not isinstance(result, str))


if __name__ == "__main__":
    unittest.main()