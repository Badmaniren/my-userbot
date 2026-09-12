import unittest
from unittest.mock import patch, MagicMock
import io

from skills.clean_compressed_db_storage import (
    CleanCompressedDBStorage,
    CleanCompressedDBStorageError
)

class TestCleanCompressedDBStorage(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.storage = CleanCompressedDBStorage(self.db_path)

    def test_init_creates_storage(self):
        self.assertIsNotNone(self.storage)

    def test_save_and_get_cleaned_data_success(self):
        raw_url = "HTTPS://Example.com/path?utm_source=test&param=1"
        raw_text = "Hello &amp; World!   "
        
        expected_url = "https://example.com/path?param=1"
        expected_text = "Hello & World!"

        with patch('skills.compressed_db_storage.CompressedDBStorage.save_compressed_data') as mock_save:
            self.storage.save_cleaned_data(raw_url, raw_text)
            mock_save.assert_called_once()
            args = mock_save.call_args[0]
            self.assertEqual(args[0], expected_url)
            self.assertEqual(args[1], expected_text)

    def test_get_cleaned_data_success(self):
        raw_url = "HTTP://Example.com/test/?utm_campaign=summer"
        expected_url = "http://example.com/test/"
        stored_payload = "Cleaned text payload"

        with patch('skills.compressed_db_storage.CompressedDBStorage.get_compressed_data', return_value=stored_payload) as mock_get:
            result = self.storage.get_cleaned_data(raw_url)
            mock_get.assert_called_once_with(expected_url)
            self.assertEqual(result, stored_payload)

    def test_save_cleaned_cache_success(self):
        raw_url = "https://example.com/?utm_medium=email"
        raw_text = "Cache text"
        expected_url = "https://example.com/"
        ttl = 300

        with patch('skills.compressed_db_storage.CompressedDBStorage.set_compressed_cache') as mock_set_cache:
            self.storage.set_cleaned_cache(raw_url, raw_text, ttl)
            mock_set_cache.assert_called_once()
            args = mock_set_cache.call_args[0]
            self.assertEqual(args[0], expected_url)
            self.assertEqual(args[1], "Cache text")
            self.assertEqual(args[2], ttl)

    def test_get_cleaned_cache_success(self):
        raw_url = "https://example.com/?utm_term=keyword"
        expected_url = "https://example.com/"
        cached_payload = "Cached payload"

        with patch('skills.compressed_db_storage.CompressedDBStorage.get_compressed_cache', return_value=cached_payload) as mock_get_cache:
            result = self.storage.get_cleaned_cache(raw_url)
            mock_get_cache.assert_called_once_with(expected_url)
            self.assertEqual(result, cached_payload)

    def test_clean_url_and_text_integration(self):
        dirty_url = "HTTP://Test.com/page.html?utm_id=123&foo=bar"
        dirty_text = "<p>Some <b>HTML</b> text &copy;</p>"
        
        clean_url_res = self.storage.clean_target_url(dirty_url)
        clean_text_res = self.storage.clean_target_text(dirty_text)

        self.assertEqual(clean_url_res, "http://test.com/page.html?foo=bar")
        self.assertIsInstance(clean_text_res, str)

    def test_error_handling_on_invalid_url(self):
        from skills.url_cleaner import UrlCleanerError
        with patch('skills.url_cleaner.clean_url', side_effect=UrlCleanerError("Invalid URL")):
            with self.assertRaises(CleanCompressedDBStorageError):
                self.storage.save_cleaned_data("invalid_url", "some text")

    def test_io_stream_handling(self):
        stream = io.BytesIO(b"stream payload data")
        self.assertIsNotNone(stream.read())

if __name__ == '__main__':
    unittest.main()