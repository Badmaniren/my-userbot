import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import socket
from skills.http_ping import check_endpoint

class TestArchitectInquisitorHttpPing(unittest.TestCase):
    
    @patch('urllib.request.urlopen')
    def test_success_200(self, mock_urlopen):
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.getcode.return_value = 200
        mock_response.headers.items.return_value = [('Content-Type', 'application/json')]
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = check_endpoint("http://example.com/api", timeout=3)
        self.assertEqual(result["status"], 200)
        self.assertIn("headers", result)

    def test_invalid_url_type_raises_type_error(self):
        with self.assertRaises(TypeError):
            check_endpoint(12345)

    def test_empty_url_raises_value_error(self):
        with self.assertRaises(ValueError):
            check_endpoint("")

    @patch('urllib.request.urlopen')
    def test_socket_timeout_returns_408(self, mock_urlopen):
        mock_urlopen.side_effect = socket.timeout("Connection timed out")

        result = check_endpoint("http://example.com/timeout", timeout=1)
        self.assertEqual(result["status"], 408)
        self.assertEqual(result["error"], "timeout")

    @patch('urllib.request.urlopen')
    def test_http_error_404_handled_gracefully(self, mock_urlopen):
        err = urllib.error.HTTPError("http://example.com/404", 404, "Not Found", {}, None)
        mock_urlopen.side_effect = err

        result = check_endpoint("http://example.com/404", timeout=5)
        self.assertEqual(result["status"], 404)
        self.assertIn("error", result)

    @patch('urllib.request.urlopen')
    def test_http_error_500_handled_gracefully(self, mock_urlopen):
        err = urllib.error.HTTPError("http://example.com/500", 500, "Internal Server Error", {}, None)
        mock_urlopen.side_effect = err

        result = check_endpoint("http://example.com/500", timeout=5)
        self.assertEqual(result["status"], 500)
        self.assertIn("error", result)

    @patch('urllib.request.urlopen')
    def test_url_error_dns_failure_handled(self, mock_urlopen):
        err = urllib.error.URLError(socket.gaierror("Name or service not known"))
        mock_urlopen.side_effect = err

        result = check_endpoint("http://nonexistent.invalid", timeout=5)
        self.assertEqual(result["status"], 503)
        self.assertIn("error", result)

    @patch('urllib.request.urlopen')
    def test_malformed_response_status_fallback(self, mock_urlopen):
        mock_response = MagicMock()
        del mock_response.status
        mock_response.getcode.return_value = None
        mock_response.headers.items.return_value = []
        mock_urlopen.return_value.__enter__.return_value = mock_response

        result = check_endpoint("http://example.com/weird", timeout=5)
        self.assertIn(result["status"], [500, 502, 503])

if __name__ == '__main__':
    unittest.main()