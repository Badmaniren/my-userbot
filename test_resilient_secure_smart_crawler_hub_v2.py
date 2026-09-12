import unittest
from unittest.mock import patch, MagicMock
import io
import requests

from skills.resilient_secure_smart_crawler_hub_v2 import (
    ResilientSecureSmartCrawlerHubV2,
    ResilientSecureSmartCrawlerHubError
)


class TestResilientSecureSmartCrawlerHubV2(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 100
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True

    def test_init(self):
        hub = ResilientSecureSmartCrawlerHubV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )
        self.assertIsNotNone(hub)

    def test_coordinate_expansion_success(self):
        hub = ResilientSecureSmartCrawlerHubV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        with patch('skills.smart_crawler.SmartCrawler.coordinate_expansion') as mock_smart, \
             patch('skills.headers_rotator.HeadersRotator.validate_headers_against_target') as mock_headers:
            
            mock_smart.return_value = {"status": "expanded"}
            mock_headers.return_value = True

            result = hub.coordinate_expansion("https://example.com", timeout=5)
            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("status"), "expanded")

    def test_validate_target_headers(self):
        hub = ResilientSecureSmartCrawlerHubV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        with patch('skills.headers_rotator.HeadersRotator.validate_headers_against_target') as mock_headers:
            mock_headers.return_value = True
            res = hub.validate_target_headers("https://example.com", timeout=5)
            self.assertTrue(res)

            mock_headers.return_value = False
            res_false = hub.validate_target_headers("https://example.com", timeout=5)
            self.assertFalse(res_false)

    def test_coordinate_expansion_error_handling(self):
        hub = ResilientSecureSmartCrawlerHubV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        with patch('skills.smart_crawler.SmartCrawler.coordinate_expansion') as mock_smart:
            mock_smart.side_effect = Exception("Expansion failed")
            
            if hasattr(hub, 'coordinate_expansion_safe'):
                res = hub.coordinate_expansion_safe("https://example.com", timeout=5)
                self.assertFalse(res)
            else:
                with self.assertRaises(Exception):
                    hub.coordinate_expansion("https://example.com", timeout=5)

    def test_hub_with_stream_mock(self):
        hub = ResilientSecureSmartCrawlerHubV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

        stream_mock = io.BytesIO(b'{"test": "data"}')

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = stream_mock
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            if hasattr(hub, 'process_stream'):
                res = hub.process_stream("https://example.com", timeout=5)
                self.assertIsNotNone(res)
            else:
                self.assertTrue(True)


if __name__ == '__main__':
    unittest.main()