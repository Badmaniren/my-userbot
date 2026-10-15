import unittest
from unittest.mock import patch, MagicMock
import urllib.error
import xml.etree.ElementTree as ET

from skills import rss_parser

class TestArchitectInquisitorRSSParser(unittest.TestCase):
    def setUp(self):
        self.valid_rss = """<?xml version="1.0" encoding="UTF-8" ?>
        <rss version="2.0">
            <channel>
                <title>Target Acquisition Feed</title>
                <link>http://example.com</link>
                <description>Free tier targets</description>
                <item>
                    <title>Target Alpha</title>
                    <link>http://example.com/target-alpha</link>
                    <description>High priority free target.</description>
                    <pubDate>Mon, 01 Jan 2024 00:00:00 GMT</pubDate>
                </item>
                <item>
                    <title>Target Beta</title>
                    <link>http://example.com/target-beta</link>
                    <description>Secondary target.</description>
                    <pubDate>Tue, 02 Jan 2024 00:00:00 GMT</pubDate>
                </item>
            </channel>
        </rss>"""

        self.valid_atom = """<?xml version="1.0" encoding="utf-8"?>
        <feed xmlns="http://www.w3.org/2005/Atom">
            <title>Atom Target Feed</title>
            <link href="http://example.com/atom"/>
            <entry>
                <title>Atom Target One</title>
                <link href="http://example.com/atom-1"/>
                <id>urn:uuid:1225c695-cfb8-4ebb-aaaa-80da344efa6a</id>
                <updated>2024-01-01T00:00:00Z</updated>
                <summary>Free tier atom target.</summary>
            </entry>
        </feed>"""

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_parse_rss_success(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.read.return_value = self.valid_rss.encode('utf-8')
        mock_ping.return_value = mock_response

        targets = rss_parser.parse_feed("http://example.com/rss", timeout=5)
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 2)
        self.assertEqual(targets[0]['title'], "Target Alpha")
        self.assertEqual(targets[0]['link'], "http://example.com/target-alpha")

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_parse_atom_success(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.read.return_value = self.valid_atom.encode('utf-8')
        mock_ping.return_value = mock_response

        targets = rss_parser.parse_feed("http://example.com/atom", timeout=5)
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 1)
        self.assertEqual(targets[0]['title'], "Atom Target One")
        self.assertEqual(targets[0]['link'], "http://example.com/atom-1")

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_network_timeout(self, mock_ping):
        mock_ping.side_effect = TimeoutError("Network operation timed out")
        with self.assertRaises(Exception):
            rss_parser.parse_feed("http://example.com/timeout", timeout=1)

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_http_error_404(self, mock_ping):
        err = urllib.error.HTTPError('http://example.com/404', 404, 'Not Found', {}, None)
        mock_ping.side_effect = err
        with self.assertRaises(Exception):
            rss_parser.parse_feed("http://example.com/404", timeout=5)

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_http_error_500(self, mock_ping):
        err = urllib.error.HTTPError('http://example.com/500', 500, 'Server Error', {}, None)
        mock_ping.side_effect = err
        with self.assertRaises(Exception):
            rss_parser.parse_feed("http://example.com/500", timeout=5)

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_malformed_xml(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.read.return_value = b"<rss><channel><title>Broken XML"
        mock_ping.return_value = mock_response

        with self.assertRaises((ET.ParseError, ValueError, Exception)):
            rss_parser.parse_feed("http://example.com/broken", timeout=5)

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_empty_feed(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.read.return_value = b""
        mock_ping.return_value = mock_response

        targets = rss_parser.parse_feed("http://example.com/empty", timeout=5)
        self.assertEqual(targets, [])

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_unexpected_payload_type(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.read.return_value = None
        mock_ping.return_value = mock_response

        with self.assertRaises(Exception):
            rss_parser.parse_feed("http://example.com/null", timeout=5)

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_unsupported_feed_structure(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.read.return_value = b"<root><unknown>data</unknown></root>"
        mock_ping.return_value = mock_response

        targets = rss_parser.parse_feed("http://example.com/unknown", timeout=5)
        self.assertEqual(targets, [])

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_fail_bad_status_code(self, mock_ping):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.read.return_value = b"Forbidden"
        mock_ping.return_value = mock_response

        with self.assertRaises(Exception):
            rss_parser.parse_feed("http://example.com/forbidden", timeout=5)

    def test_parse_raw_string(self):
        targets = rss_parser.parse_feed(self.valid_rss)
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 2)
        self.assertEqual(targets[0]['title'], "Target Alpha")

    def test_parse_raw_bytes(self):
        targets = rss_parser.parse_feed(self.valid_rss.encode('utf-8'))
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 2)
        self.assertEqual(targets[0]['title'], "Target Alpha")

    def test_parse_dict_with_data_key(self):
        payload = {"status": 200, "data": self.valid_atom}
        targets = rss_parser.parse_feed(payload)
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 1)
        self.assertEqual(targets[0]['title'], "Atom Target One")

    def test_parse_dict_with_text_key(self):
        payload = {"status_code": 200, "text": self.valid_rss}
        targets = rss_parser.parse_feed(payload)
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 2)

    def test_parse_object_with_read(self):
        class DummyResponse:
            def read(self):
                return self.valid_atom

        dummy = DummyResponse()
        dummy.valid_atom = self.valid_atom

        targets = rss_parser.parse_feed(dummy)
        self.assertIsInstance(targets, list)
        self.assertGreaterEqual(len(targets), 1)
        self.assertEqual(targets[0]['title'], "Atom Target One")

    @patch('skills.rss_parser.cached_ping.ping_and_cache')
    def test_url_fetch_returning_dict(self, mock_ping):
        mock_ping.return_value = {"status": 200, "data": self.valid_rss}
        targets = rss_parser.parse_feed("http://example.com/mock-dict")
        self.assertIsInstance(targets, list)
        self.assertEqual(targets[0]['title'], "Target Alpha")

if __name__ == '__main__':
    unittest.main()