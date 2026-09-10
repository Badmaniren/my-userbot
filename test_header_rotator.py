import unittest
from unittest.mock import patch, MagicMock
from skills.header_rotator import HeaderRotator


class TestHeaderRotatorInquisitor(unittest.TestCase):
    def setUp(self):
        self.rotator = HeaderRotator()

    def test_get_headers_returns_valid_structure(self):
        headers = self.rotator.get_headers()
        self.assertIsInstance(headers, dict)
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept-Language", headers)

    def test_pool_contains_multiple_unique_agents(self):
        agents = {self.rotator.get_headers()["User-Agent"] for _ in range(50)}
        self.assertGreater(len(agents), 1, "Пул UA слишком убог, Cloudflare нас сожрет!")

    def test_empty_or_corrupted_pool_recovery(self):
        self.rotator.user_agents = []
        headers = self.rotator.get_headers()
        self.assertIn("User-Agent", headers)
        self.assertGreater(len(headers["User-Agent"]), 0)

    @patch("skills.header_rotator.file_cache.FileCache")
    def test_cache_integration_valid_data(self, mock_file_cache_class):
        mock_cache = mock_file_cache_class.return_value
        mock_cache.get.return_value = ["Agent-X", "Agent-Y"]
        
        rotator = HeaderRotator(use_cache=True)
        ua = rotator._load_user_agents()
        self.assertIn("Agent-X", ua)

    @patch("skills.header_rotator.file_cache.FileCache")
    def test_cache_failure_corrupted_data(self, mock_file_cache_class):
        mock_cache = mock_file_cache_class.return_value
        mock_cache.get.return_value = None
        
        rotator = HeaderRotator(use_cache=True)
        ua = rotator._load_user_agents()
        self.assertIsInstance(ua, list)
        self.assertGreater(len(ua), 0, "Кэш отдал пустышку, ротатор должен поднять дефолтный пул!")

    @patch("skills.header_rotator.http_ping.check_endpoint")
    def test_endpoint_validation_success(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.status = 200
        mock_resp.getcode.return_value = 200
        mock_check.return_value = mock_resp

        result = self.rotator.validate_agent("Mozilla/5.0")
        self.assertTrue(result)

    @patch("skills.header_rotator.http_ping.check_endpoint")
    def test_endpoint_validation_server_error_500(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.status = 500
        mock_resp.getcode.return_value = 500
        mock_check.return_value = mock_resp

        result = self.rotator.validate_agent("Mozilla/5.0")
        self.assertFalse(result)

    @patch("skills.header_rotator.http_ping.check_endpoint")
    def test_endpoint_validation_not_found_404(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.status = 404
        mock_resp.getcode.return_value = 404
        mock_check.return_value = mock_resp

        result = self.rotator.validate_agent("Mozilla/5.0")
        self.assertFalse(result)

    @patch("skills.header_rotator.http_ping.check_endpoint")
    def test_endpoint_validation_timeout(self, mock_check):
        mock_check.side_effect = TimeoutError("Network timeout")

        result = self.rotator.validate_agent("Mozilla/5.0")
        self.assertFalse(result)

    def test_clean_text_integration_with_headers(self):
        dirty_agent = "  Mozilla/5.0 (Windows NT 10.0) \n\t"
        cleaned = self.rotator.sanitize_agent(dirty_agent)
        self.assertEqual(cleaned, "Mozilla/5.0 (Windows NT 10.0)")

    @patch("skills.header_rotator.cached_ping.ping_and_cache")
    def test_cached_ping_failure_handling(self, mock_ping):
        mock_ping.side_effect = Exception("Cloudflare blocked us")
        
        headers = self.rotator.get_headers_with_ping("http://example.com")
        self.assertIsInstance(headers, dict)
        self.assertIn("User-Agent", headers)


if __name__ == "__main__":
    unittest.main()