import unittest
from unittest.mock import patch, MagicMock
from html.parser import HTMLParser

from skills.link_extractor import LinkExtractor


class TestLinkExtractorInquisitor(unittest.TestCase):
    
    def setUp(self):
        self.extractor = LinkExtractor()

    def test_extract_valid_links(self):
        html_content = '<html><body><a href="https://example.com/page1">Link 1</a><a href="/page2">Link 2</a></body></html>'
        links = self.extractor.extract(html_content)
        self.assertIn("https://example.com/page1", links)
        self.assertIn("/page2", links)
        self.assertEqual(len(links), 2)

    def test_extract_empty_input(self):
        self.assertEqual(self.extractor.extract(""), [])

    def test_extract_none_input(self):
        with self.assertRaises((TypeError, AttributeError)):
            self.extractor.extract(None)

    def test_extract_malformed_html(self):
        html_content = '<a href="https://broken.com">Unclosed tag'
        links = self.extractor.extract(html_content)
        self.assertEqual(links, ["https://broken.com"])

    def test_extract_no_links(self):
        html_content = '<html><body><p>No links here, just text.</p></body></html>'
        self.assertEqual(self.extractor.extract(html_content), [])

    @patch('skills.link_extractor.check_endpoint')
    def test_validate_link_success(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.status = 200
        mock_check.return_value = mock_resp

        result = self.extractor.validate_link("https://example.com", timeout=5)
        self.assertTrue(result)
        mock_check.assert_called_once_with("https://example.com", 5)

    @patch('skills.link_extractor.check_endpoint')
    def test_validate_link_404_failure(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 404
        mock_resp.status = 404
        mock_check.return_value = mock_resp

        result = self.extractor.validate_link("https://example.com/not-found", timeout=5)
        self.assertFalse(result)

    @patch('skills.link_extractor.check_endpoint')
    def test_validate_link_500_server_error(self, mock_check):
        mock_resp = MagicMock()
        mock_resp.status_code = 500
        mock_resp.status = 500
        mock_check.return_value = mock_resp

        result = self.extractor.validate_link("https://example.com/error", timeout=5)
        self.assertFalse(result)

    @patch('skills.link_extractor.check_endpoint')
    def test_validate_link_network_exception(self, mock_check):
        mock_check.side_effect = ConnectionError("Network unreachable")

        result = self.extractor.validate_link("https://dead-domain.com", timeout=2)
        self.assertFalse(result)

    @patch('skills.link_extractor.ping_and_cache')
    def test_cached_extract_and_ping_success(self, mock_ping_cache):
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.status = 200
        mock_ping_cache.return_value = mock_resp

        result = self.extractor.process_with_cache("https://cached.com", 3)
        self.assertTrue(result)
        mock_ping_cache.assert_called_once_with("https://cached.com", 3)

    @patch('skills.link_extractor.ping_and_cache')
    def test_cached_extract_and_ping_timeout(self, mock_ping_cache):
        mock_ping_cache.side_effect = TimeoutError("Ping timeout")

        result = self.extractor.process_with_cache("https://slow.com", 1)
        self.assertFalse(result)

    def test_extract_with_dirty_text_input(self):
        html_content = '<a href="javascript:alert(1)">XSS</a><a href="https://safe.com">Safe</a>'
        links = self.extractor.extract(html_content)
        self.assertIn("https://safe.com", links)
        self.assertIn("javascript:alert(1)", links)


if __name__ == '__main__':
    unittest.main()