import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_global_mesh_node_v1 import (
    ResilientSecureSmartCrawlerHubV11GlobalMesh,
    ResilientSecureSmartCrawlerHubV11GlobalMeshError
)

class TestResilientSecureSmartCrawlerHubV11GlobalMesh(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.node = ResilientSecureSmartCrawlerHubV11GlobalMesh(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_init_node(self):
        self.assertIsInstance(self.node, ResilientSecureSmartCrawlerHubV11GlobalMesh)

    def test_validate_target_headers_success(self):
        url = "https://example.com/mesh-node"
        timeout = 5
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            res = self.node.validate_target_headers(url, timeout)
            self.assertTrue(res)

    def test_validate_target_headers_failure(self):
        url = "https://example.com/mesh-node"
        timeout = 5
        with patch('requests.head', side_effect=Exception("Connection error")):
            res = self.node.validate_target_headers(url, timeout)
            self.assertFalse(res)

    def test_coordinate_expansion_success(self):
        url = "https://example.com/mesh-expand"
        timeout = 5
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = io.BytesIO(b'{"status": "ok"}')
            mock_get.return_value = mock_response

            res = self.node.coordinate_expansion(url, timeout)
            self.assertTrue(res)

    def test_coordinate_expansion_failure(self):
        url = "https://example.com/mesh-expand"
        timeout = 5
        with patch('requests.get', side_effect=Exception("Expansion failed")):
            with self.assertRaises((ResilientSecureSmartCrawlerHubV11GlobalMeshError, Exception)):
                self.node.coordinate_expansion(url, timeout)

    def test_coordinate_expansion_safe_success(self):
        url = "https://example.com/mesh-expand"
        timeout = 5
        with patch.object(self.node, 'coordinate_expansion', return_value=True) as mock_coord:
            res = self.node.coordinate_expansion_safe(url, timeout)
            self.assertTrue(res)
            mock_coord.assert_called_once_with(url, timeout)

    def test_coordinate_expansion_safe_caught_exception(self):
        url = "https://example.com/mesh-expand"
        timeout = 5
        with patch.object(self.node, 'coordinate_expansion', side_effect=Exception("Boom")):
            res = self.node.coordinate_expansion_safe(url, timeout)
            self.assertFalse(res)

    def test_export_and_get_exported_report(self):
        target = "node_alpha"
        report_data = {"metrics": "nominal", "sync": True}
        
        self.node.export_analytics_report(target, report_data)
        retrieved_report = self.node.get_exported_report(target)
        
        self.assertEqual(retrieved_report, report_data)

    def test_process_stream_success(self):
        url = "https://example.com/mesh-stream"
        timeout = 5
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = io.BytesIO(b'stream_data')
            mock_get.return_value = mock_response

            try:
                self.node.process_stream(url, timeout)
            except Exception as e:
                self.fail(f"process_stream raised unexpected exception: {e}")

    def test_process_stream_error(self):
        url = "https://example.com/mesh-stream"
        timeout = 5
        with patch('requests.get', side_effect=Exception("Stream down")):
            with self.assertRaises((ResilientSecureSmartCrawlerHubV11GlobalMeshError, Exception)):
                self.node.process_stream(url, timeout)

if __name__ == '__main__':
    unittest.main()