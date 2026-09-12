import unittest
from unittest.mock import patch, MagicMock
import io

from skills.clean_compressed_sitemap_parser_v3 import (
    CleanCompressedSitemapParserV3,
    CleanCompressedSitemapParserError,
)
from skills.clean_sitemap_parser_v2 import CleanSitemapParserError
from skills.clean_compressed_db_storage import CleanCompressedDBStorageError


class TestCleanCompressedSitemapParserV3(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.parser = CleanCompressedSitemapParserV3(db_path=self.db_path)

    def test_init_composition_success(self):
        self.assertIsNotNone(self.parser)
        self.assertIsNotNone(self.parser.sitemap_parser)
        self.assertIsNotNone(self.parser.storage)

    def test_parse_success_with_caching(self):
        url = "https://example.com/sitemap.xml"
        timeout = 5
        mock_links = ["https://example.com/page1?utm_source=test", "https://example.com/page2"]

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.parse") as mock_parse, \
             patch("skills.clean_compressed_db_storage.CleanCompressedDBStorage.get_cleaned_and_compressed_data") as mock_get_cache, \
             patch("skills.clean_compressed_db_storage.CleanCompressedDBStorage.set_cleaned_compressed_cache") as mock_set_cache:

            mock_get_cache.return_value = None
            mock_parse.return_value = mock_links

            result = self.parser.parse(url, timeout)

            self.assertIsInstance(result, list)
            self.assertEqual(len(result), 2)
            mock_parse.assert_called_once_with(url, timeout)
            mock_get_cache.assert_called_once()
            mock_set_cache.assert_called_once()

    def test_parse_cache_hit(self):
        url = "https://example.com/sitemap.xml"
        timeout = 5
        cached_payload = ["https://example.com/cached1", "https://example.com/cached2"]

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.parse") as mock_parse, \
             patch("skills.clean_compressed_db_storage.CleanCompressedDBStorage.get_cleaned_and_compressed_data") as mock_get_cache:

            mock_get_cache.return_value = cached_payload

            result = self.parser.parse(url, timeout)

            self.assertEqual(result, cached_payload)
            mock_parse.assert_not_called()

    def test_validate_sitemap_true(self):
        url = "https://example.com/sitemap.xml"
        timeout = 5

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.validate_sitemap") as mock_validate:
            mock_validate.return_value = True
            res = self.parser.validate_sitemap(url, timeout)
            self.assertTrue(res)
            mock_validate.assert_called_once_with(url, timeout)

    def test_validate_sitemap_false(self):
        url = "https://example.com/invalid_sitemap.xml"
        timeout = 5

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.validate_sitemap") as mock_validate:
            mock_validate.return_value = False
            res = self.parser.validate_sitemap(url, timeout)
            self.assertFalse(res)

    def test_validate_sitemap_handles_exception(self):
        url = "https://example.com/error_sitemap.xml"
        timeout = 5

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.validate_sitemap") as mock_validate:
            mock_validate.side_effect = CleanSitemapParserError("Parsing error")
            res = self.parser.validate_sitemap(url, timeout)
            self.assertFalse(res)

    def test_parse_and_clean_success(self):
        url = "https://example.com/sitemap.xml"
        timeout = 5
        raw_links = ["https://example.com/page1?utm_source=google", "https://example.com/page2/"]

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.parse_and_clean") as mock_parse_clean, \
             patch("skills.clean_compressed_db_storage.CleanCompressedDBStorage.save_cleaned_and_compressed_data") as mock_save:

            mock_parse_clean.return_value = raw_links

            result = self.parser.parse_and_clean(url, timeout)

            self.assertIsInstance(result, list)
            mock_parse_clean.assert_called_once_with(url, timeout)
            mock_save.assert_called_once()

    def test_parse_and_clean_raises_custom_error(self):
        url = "https://example.com/bad_sitemap.xml"
        timeout = 5

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.parse_and_clean") as mock_parse_clean:
            mock_parse_clean.side_effect = Exception("Critical failure")

            with self.assertRaises(CleanCompressedSitemapParserError):
                self.parser.parse_and_clean(url, timeout)

    def test_storage_interaction_error(self):
        url = "https://example.com/sitemap.xml"
        timeout = 5
        mock_links = ["https://example.com/page1"]

        with patch("skills.clean_sitemap_parser_v2.CleanSitemapParser.parse") as mock_parse, \
             patch("skills.clean_compressed_db_storage.CleanCompressedDBStorage.get_cleaned_and_compressed_data") as mock_get_cache, \
             patch("skills.clean_compressed_db_storage.CleanCompressedDBStorage.set_cleaned_compressed_cache") as mock_set_cache:

            mock_get_cache.return_value = None
            mock_parse.return_value = mock_links
            mock_set_cache.side_effect = CleanCompressedDBStorageError("DB error")

            result = self.parser.parse(url, timeout)
            self.assertEqual(result, mock_links)


if __name__ == "__main__":
    unittest.main()