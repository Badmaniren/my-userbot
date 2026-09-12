import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_smart_aggregator_v6 import (
    ResilientSecureSmartAggregatorV6,
    ResilientSecureSmartAggregatorV6Error
)

class TestResilientSecureSmartAggregatorV6(unittest.TestCase):
    def setUp(self):
        self.aggregator = ResilientSecureSmartAggregatorV6(
            db_path=":memory:",
            max_memory_mb=128,
            calls=5,
            period=1.0,
            raise_on_limit=True
        )

    def test_init(self):
        self.assertIsNotNone(self.aggregator.hub)
        self.assertIsNotNone(self.aggregator.storage)
        self.assertEqual(self.aggregator.max_memory_mb, 128)
        self.assertTrue(self.aggregator.raise_on_limit)

    def test_coordinate_expansion_success_dict(self):
        test_url = "https://example.com/api"
        test_data = {"data": "some structured payload"}

        with patch.object(self.aggregator.hub, 'coordinate_expansion', return_value=test_data) as mock_hub_coord:
            result = self.aggregator.coordinate_expansion(test_url, timeout=5.0)
            mock_hub_coord.assert_called_once_with(test_url, timeout=5.0)
            self.assertEqual(result, test_data)

    def test_coordinate_expansion_success_string(self):
        test_url = "https://example.com/page"
        test_data = "plain text result"

        with patch.object(self.aggregator.hub, 'coordinate_expansion', return_value=test_data) as mock_hub_coord:
            result = self.aggregator.coordinate_expansion(test_url, timeout=3.0)
            mock_hub_coord.assert_called_once_with(test_url, timeout=3.0)
            self.assertEqual(result, test_data)

    def test_coordinate_expansion_none_result(self):
        test_url = "https://example.com/none"

        with patch.object(self.aggregator.hub, 'coordinate_expansion', return_value=None) as mock_hub_coord:
            result = self.aggregator.coordinate_expansion(test_url, timeout=2.0)
            mock_hub_coord.assert_called_once_with(test_url, timeout=2.0)
            self.assertIsNone(result)

    def test_coordinate_expansion_raises_error(self):
        test_url = "https://example.com/error"

        with patch.object(self.aggregator.hub, 'coordinate_expansion', side_effect=Exception("Hub failure")):
            with self.assertRaises(ResilientSecureSmartAggregatorV6Error):
                self.aggregator.coordinate_expansion(test_url, timeout=1.0)

    def test_coordinate_expansion_safe_true(self):
        test_url = "https://example.com/safe"

        with patch.object(self.aggregator.hub, 'coordinate_expansion_safe', return_value=True) as mock_safe:
            res = self.aggregator.coordinate_expansion_safe(test_url, timeout=2.0)
            mock_safe.assert_called_once_with(test_url, timeout=2.0)
            self.assertTrue(res)

    def test_coordinate_expansion_safe_false(self):
        test_url = "https://example.com/unsafe"

        with patch.object(self.aggregator.hub, 'coordinate_expansion_safe', return_value=False) as mock_safe:
            res = self.aggregator.coordinate_expansion_safe(test_url, timeout=2.0)
            mock_safe.assert_called_once_with(test_url, timeout=2.0)
            self.assertFalse(res)

    def test_validate_target_headers_true(self):
        test_url = "https://example.com/headers"

        with patch.object(self.aggregator.hub, 'validate_target_headers', return_value=True) as mock_headers:
            res = self.aggregator.validate_target_headers(test_url, timeout=5.0)
            mock_headers.assert_called_once_with(test_url, timeout=5.0)
            self.assertTrue(res)

    def test_validate_target_headers_false(self):
        test_url = "https://example.com/headers"

        with patch.object(self.aggregator.hub, 'validate_target_headers', return_value=False) as mock_headers:
            res = self.aggregator.validate_target_headers(test_url, timeout=5.0)
            mock_headers.assert_called_once_with(test_url, timeout=5.0)
            self.assertFalse(res)

    def test_process_stream_success(self):
        test_url = "https://example.com/stream"
        mock_stream = io.BytesIO(b'stream chunk data')

        with patch.object(self.aggregator.hub, 'process_stream', return_value=mock_stream) as mock_stream_call:
            res = self.aggregator.process_stream(test_url, timeout=10.0)
            mock_stream_call.assert_called_once_with(test_url, timeout=10.0)
            self.assertEqual(res.read(), b'stream chunk data')

    def test_process_stream_failure(self):
        test_url = "https://example.com/stream-error"

        with patch.object(self.aggregator.hub, 'process_stream', side_effect=Exception("Stream drop")):
            with self.assertRaises(ResilientSecureSmartAggregatorV6Error):
                self.aggregator.process_stream(test_url, timeout=5.0)

if __name__ == '__main__':
    unittest.main()