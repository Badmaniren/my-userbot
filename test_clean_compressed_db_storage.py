import unittest
from unittest.mock import patch, MagicMock
from skills.clean_compressed_db_storage import CleanCompressedDBStorage, CleanCompressedDBStorageError
from skills.url_cleaner import UrlCleanerError

class TestCleanCompressedDBStorage(unittest.TestCase):
    def setUp(self):
        self.db_path = ":memory:"
        self.processor = CleanCompressedDBStorage(self.db_path)

    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_clean_target_url_success(self, mock_clean_url):
        mock_clean_url.return_value = "https://example.com"
        result = self.processor.clean_target_url("https://example.com/?utm_source=test")
        self.assertEqual(result, "https://example.com")
        mock_clean_url.assert_called_once_with("https://example.com/?utm_source=test")

    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_clean_target_url_error(self, mock_clean_url):
        mock_clean_url.side_effect = UrlCleanerError("Invalid URL")
        with self.assertRaises(UrlCleanerError):
            self.processor.clean_target_url("invalid-url")

    @patch('skills.clean_compressed_db_storage.clean')
    def test_clean_target_text(self, mock_clean):
        mock_clean.return_value = "Hello &amp; welcome"
        result = self.processor.clean_target_text("<b>Hello &amp; welcome</b>")
        self.assertEqual(result, "Hello & welcome")

    @patch('skills.clean_compressed_db_storage.clean')
    def test_clean_target_text_exception_fallback(self, mock_clean):
        mock_clean.side_effect = Exception("Parsing error")
        raw_text = "fallback text"
        result = self.processor.clean_target_text(raw_text)
        self.assertEqual(result, raw_text)

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.save_compressed_data')
    @patch('skills.clean_compressed_db_storage.clean')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_save_cleaned_data_success(self, mock_clean_url, mock_clean, mock_save):
        mock_clean_url.return_value = "https://example.com"
        mock_clean.return_value = "Clean text"
        
        self.processor.save_cleaned_data("https://example.com", "<p>Clean text</p>")
        mock_save.assert_called_once_with("https://example.com", "Clean text")

    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_error_handling_on_invalid_url(self, mock_clean_url):
        mock_clean_url.side_effect = UrlCleanerError("Bad URL")
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.save_cleaned_data("bad-url", "some text")

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_data')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_get_cleaned_data_success(self, mock_clean_url, mock_get):
        mock_clean_url.return_value = "https://example.com"
        mock_get.return_value = "Stored data"
        
        result = self.processor.get_cleaned_data("https://example.com")
        self.assertEqual(result, "Stored data")
        mock_get.assert_called_once_with("https://example.com")

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_data')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_get_cleaned_data_error(self, mock_clean_url, mock_get):
        mock_clean_url.return_value = "https://example.com"
        mock_get.side_effect = Exception("DB error")
        
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.get_cleaned_data("https://example.com")

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.set_compressed_cache')
    @patch('skills.clean_compressed_db_storage.clean')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_set_cleaned_cache_success(self, mock_clean_url, mock_clean, mock_set_cache):
        mock_clean_url.return_value = "https://example.com"
        mock_clean.return_value = "Cached text"
        
        self.processor.set_cleaned_cache("https://example.com", "Cached text", 3600)
        mock_set_cache.assert_called_once_with("https://example.com", "Cached text", 3600)

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.set_compressed_cache')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_set_cleaned_cache_error(self, mock_clean_url, mock_set_cache):
        mock_clean_url.return_value = "https://example.com"
        mock_set_cache.side_effect = Exception("Cache error")
        
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.set_cleaned_cache("https://example.com", "text", 3600)

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_cache')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_get_cleaned_cache_success(self, mock_clean_url, mock_get_cache):
        mock_clean_url.return_value = "https://example.com"
        mock_get_cache.return_value = "Cached payload"
        
        result = self.processor.get_cleaned_cache("https://example.com")
        self.assertEqual(result, "Cached payload")
        mock_get_cache.assert_called_once_with("https://example.com")

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_cache')
    @patch('skills.clean_compressed_db_storage.clean_url')
    def test_get_cleaned_cache_error(self, mock_clean_url, mock_get_cache):
        mock_clean_url.return_value = "https://example.com"
        mock_get_cache.side_effect = Exception("Cache error")
        
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.get_cleaned_cache("https://example.com")

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.save_compressed_data')
    def test_save_cleaned_and_compressed_data_success(self, mock_save):
        payload = {"key": "value"}
        self.processor.save_cleaned_and_compressed_data("https://example.com", payload)
        mock_save.assert_called_once_with("https://example.com", payload)

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.save_compressed_data')
    def test_save_cleaned_and_compressed_data_error(self, mock_save):
        mock_save.side_effect = Exception("Storage fail")
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.save_cleaned_and_compressed_data("https://example.com", {})

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_data')
    def test_get_cleaned_and_compressed_data_success(self, mock_get):
        mock_get.return_value = {"key": "value"}
        result = self.processor.get_cleaned_and_compressed_data("https://example.com")
        self.assertEqual(result, {"key": "value"})

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_data')
    def test_get_cleaned_and_compressed_data_error(self, mock_get):
        mock_get.side_effect = Exception("Storage fail")
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.get_cleaned_and_compressed_data("https://example.com")

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.set_compressed_cache')
    def test_set_cleaned_compressed_cache_success(self, mock_set):
        payload = {"data": 123}
        self.processor.set_cleaned_compressed_cache("https://example.com", payload, 60)
        mock_set.assert_called_once_with("https://example.com", payload, 60)

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.set_compressed_cache')
    def test_set_cleaned_compressed_cache_error(self, mock_set):
        mock_set.side_effect = Exception("Cache fail")
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.set_cleaned_compressed_cache("https://example.com", {}, 60)

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_cache')
    def test_get_cleaned_compressed_cache_success(self, mock_get):
        mock_get.return_value = {"data": 123}
        result = self.processor.get_cleaned_compressed_cache("https://example.com")
        self.assertEqual(result, {"data": 123})

    @patch('skills.clean_compressed_db_storage.CompressedDBStorage.get_compressed_cache')
    def test_get_cleaned_compressed_cache_error(self, mock_get):
        mock_get.side_effect = Exception("Cache fail")
        with self.assertRaises(CleanCompressedDBStorageError):
            self.processor.get_cleaned_compressed_cache("https://example.com")

if __name__ == '__main__':
    unittest.main()