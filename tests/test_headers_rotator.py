import unittest
from unittest.mock import patch, MagicMock
from skills.headers_rotator import HeadersRotator

class TestHeadersRotatorInquisitor(unittest.TestCase):

    def setUp(self):
        self.rotator = HeadersRotator()

    def test_get_random_user_agent_success(self):
        ua = self.rotator.get_random_user_agent()
        self.assertIsInstance(ua, str)
        self.assertGreater(len(ua), 0)

    def test_rotate_headers_returns_dict(self):
        headers = self.rotator.rotate_headers()
        self.assertIsInstance(headers, dict)
        self.assertIn("User-Agent", headers)
        self.assertIn("Accept-Language", headers)

    @patch("skills.headers_rotator.http_ping.check_endpoint")
    def test_bypass_check_success_200(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.status = 200
        mock_check.return_value = mock_resp

        result = self.rotator.validate_headers_against_target("https://target.com/api", timeout=5)
        self.assertTrue(result)
        mock_check.assert_called_once()

    @patch("skills.headers_rotator.http_ping.check_endpoint")
    def test_bypass_check_fails_403_cloudflare(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 403
        mock_resp.status = 403
        mock_check.return_value = mock_resp

        result = self.rotator.validate_headers_against_target("https://target.com/api", timeout=5)
        self.assertFalse(result)

    @patch("skills.headers_rotator.http_ping.check_endpoint")
    def test_bypass_check_fails_500_server_error(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.status = 500
        mock_check.return_value = mock_resp

        result = self.rotator.validate_headers_against_target("https://target.com/api", timeout=5)
        self.assertFalse(result)

    @patch("skills.headers_rotator.http_ping.check_endpoint")
    def test_bypass_check_network_exception(self, mock_check):
        mock_check.side_effect = Exception("Network unreachable")

        result = self.rotator.validate_headers_against_target("https://target.com/api", timeout=5)
        self.assertFalse(result)

    def test_invalid_url_input_type(self):
        with self.assertRaises((ValueError, TypeError)):
            self.rotator.validate_headers_against_target(None, timeout=5)

        with self.assertRaises((ValueError, TypeError)):
            self.rotator.validate_headers_against_target(12345, timeout=5)

    def test_empty_url_string(self):
        with self.assertRaises((ValueError, TypeError)):
            self.rotator.validate_headers_against_target("", timeout=5)

    @patch("skills.headers_rotator.file_cache.FileCache")
    def test_cache_integration_failure(self, mock_cache_class):
        mock_cache_instance = MagicMock()
        mock_cache_instance.get.side_effect = Exception("Cache corruption")
        mock_cache_class.return_value = mock_cache_instance

        rotator_with_cache = HeadersRotator(cache_enabled=True)
        headers = rotator_with_cache.rotate_headers()
        self.assertIsInstance(headers, dict)

    @patch("skills.headers_rotator.clean_text.clean")
    def test_user_agent_cleaning_injection(self, mock_clean):
        mock_clean.return_value = "Sanitized-Agent"
        ua = self.rotator.get_sanitized_user_agent("<script>alert(1)</script>")
        self.assertEqual(ua, "Sanitized-Agent")
        mock_clean.assert_called_once()

    def test_negative_timeout_handling(self):
        with self.assertRaises((ValueError, TypeError)):
            self.rotator.validate_headers_against_target("https://target.com", timeout=-1)

if __name__ == "__main__":
    unittest.main()