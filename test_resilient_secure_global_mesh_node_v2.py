import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_ global_mesh_node_v2 import (
    ResilientSecureGlobalMeshNodeV2,
    ResilientSecureGlobalMeshNodeV2Error
)

class TestResilientSecureGlobalMeshNodeV2(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.node = ResilientSecureGlobalMeshNodeV2(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_initialization(self):
        self.assertIsInstance(self.node, ResilientSecureGlobalMeshNodeV2)

    def test_validate_target_headers_success(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            result = self.node.validate_target_headers("https://example.com", 5)
            self.assertTrue(result)

    def test_validate_target_headers_failure(self):
        with patch('requests.head') as mock_head:
            mock_head.side_effect = Exception("Connection error")

            result = self.node.validate_target_headers("https://example.com", 5)
            self.assertFalse(result)

    def test_coordinate_expansion_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = io.BytesIO(b'{"status": "ok"}')
            mock_get.return_value = mock_response

            result = self.node.coordinate_expansion("https://example.com/mesh", 5)
            self.assertTrue(result)

    def test_coordinate_expansion_safe(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Mesh failure")

            result = self.node.coordinate_expansion_safe("https://example.com/mesh", 5)
            self.assertFalse(result)

    def test_export_and_get_analytics_report(self):
        target = "https://example.com/node"
        report_data = {"mesh_sync": True, "latency_ms": 12}

        self.node.export_analytics_report(target, report_data)
        exported = self.node.get_exported_report(target)

        self.assertEqual(exported, report_data)

    def test_process_stream(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.iter_content.return_value = [b'stream_chunk']
            mock_get.return_value = mock_response

            try:
                self.node.process_stream("https://example.com/stream", 5)
            except Exception as e:
                self.fail(f"process_stream raised unexpected exception: {e}")

    def test_error_handling_exception(self):
        with self.assertRaises(ResilientSecureGlobalMeshNodeV2Error):
            raise ResilientSecureGlobalMeshNodeV2Error("Critical Mesh Error")

if __name__ == '__main__':
    unittest.main()