import unittest
from unittest.mock import patch, MagicMock
import urllib.error
from skills.http_ping import check_endpoint


class TestHttpPingInquisitor(unittest.TestCase):

    def test_invalid_url_type_raises_exception(self):
        with self.assertRaises((TypeError, ValueError)):
            check_endpoint(url=12345)

    def test_empty_url_string_fails(self):
        with self.assertRaises((ValueError, urllib.error.URLError)):
            check_endpoint(url="")

    @patch("skills.http_ping.urllib.request.urlopen")
    def test_endpoint_success_returns_dict(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = [("Content-Type", "application/json")]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = check_endpoint(url="https://api.free-endpoints.com/test", timeout=2)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], 200)

    @patch("skills.http_ping.urllib.request.urlopen")
    def test_endpoint_timeout_handled(self, mock_urlopen):
        import socket
        mock_urlopen.side_effect = socket.timeout("Connection timed out")

        result = check_endpoint(url="https://slow-api.com", timeout=1)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), 408) or self.assertIn("error", result)

    @patch("skills.http_ping.urllib.request.urlopen")
    def test_malformed_url_raises_error(self, mock_urlopen):
        mock_urlopen.side_effect = ValueError("Unknown url type")

        with self.assertRaises((ValueError, urllib.error.URLError)):
            check_endpoint(url="htpt:/not-a-url")


if __name__ == "__main__":
    unittest.main()