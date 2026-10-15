import unittest
from unittest.mock import patch, MagicMock
from skills.cached_ping import ping_and_cache


class TestCachedPing(unittest.TestCase):

    @patch('skills.cached_ping.FileCache')
    @patch('skills.cached_ping.check_endpoint')
    def test_cache_hit_returns_cached_data_without_ping(self, mock_check, mock_file_cache_cls):
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = {"status": 200, "response_time": 0.1}
        mock_file_cache_cls.return_value = mock_cache_instance

        url = "http://example.com"
        result = ping_and_cache(url)

        mock_cache_instance.get.assert_called_once_with(url)
        mock_check.assert_not_called()
        self.assertEqual(result, {"status": 200, "response_time": 0.1})

    @patch('skills.cached_ping.FileCache')
    @patch('skills.cached_ping.check_endpoint')
    def test_cache_miss_fetches_and_caches_result(self, mock_check, mock_file_cache_cls):
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_file_cache_cls.return_value = mock_cache_instance

        ping_response = {"status": 200, "response_time": 0.25}
        mock_check.return_value = ping_response

        url = "http://api.service.org/health"
        result = ping_and_cache(url, timeout=10)

        mock_cache_instance.get.assert_called_once_with(url)
        mock_check.assert_called_once_with(url, 10)
        mock_cache_instance.set.assert_called_once_with(url, ping_response)
        self.assertEqual(result, ping_response)

    @patch('skills.cached_ping.FileCache')
    @patch('skills.cached_ping.check_endpoint')
    def test_default_timeout_argument(self, mock_check, mock_file_cache_cls):
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_file_cache_cls.return_value = mock_cache_instance
        mock_check.return_value = {"status": 200}

        url = "http://test.local"
        ping_and_cache(url)

        mock_check.assert_called_once_with(url, 5)

    @patch('skills.cached_ping.FileCache')
    @patch('skills.cached_ping.check_endpoint')
    def test_empty_url_input(self, mock_check, mock_file_cache_cls):
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_file_cache_cls.return_value = mock_cache_instance
        mock_check.return_value = {"status": 400, "error": "Empty URL"}

        url = ""
        result = ping_and_cache(url)

        mock_cache_instance.get.assert_called_once_with("")
        mock_check.assert_called_once_with("", 5)
        mock_cache_instance.set.assert_called_once_with("", {"status": 400, "error": "Empty URL"})
        self.assertIsInstance(result, dict)
        self.assertEqual(result, {"status": 400, "error": "Empty URL"})

    @patch('skills.cached_ping.FileCache')
    @patch('skills.cached_ping.check_endpoint')
    def test_ping_exception_propagation(self, mock_check, mock_file_cache_cls):
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.return_value = None
        mock_file_cache_cls.return_value = mock_cache_instance
        mock_check.side_effect = TimeoutError("Request timed out")

        url = "http://timeout.com"
        with self.assertRaises(TimeoutError):
            ping_and_cache(url)


if __name__ == '__main__':
    unittest.main()