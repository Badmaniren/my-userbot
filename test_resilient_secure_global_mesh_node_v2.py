import unittest
from unittest.mock import patch, MagicMock
import io
import requests

from skills.resilient_secure_global_mesh_node_v2 import (
    ResilientSecureGlobalMeshNodeV2,
    ResilientSecureGlobalMeshNodeV2Error
)

class TestResilientSecureGlobalMeshNodeV2(unittest.TestCase):

    def setUp(self):
        self.node = ResilientSecureGlobalMeshNodeV2(
            db_path=":memory:",
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_init_inheritance_and_attributes(self):
        self.assertIsInstance(self.node, ResilientSecureGlobalMeshNodeV2)
        self.assertIsNotNone(self.node.analytics_exporter)
        self.assertIsInstance(self.node._exported_reports, dict)

    @patch('requests.head')
    def test_validate_target_headers_success(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_head.return_value = mock_response

        url = "http://example.com"
        result = self.node.validate_target_headers(url, timeout=5)
        self.assertTrue(result)
        mock_head.assert_called_once_with(url, timeout=5)

    @patch('requests.head')
    def test_validate_target_headers_failure(self, mock_head):
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_head.return_value = mock_response

        url = "http://example.com/404"
        result = self.node.validate_target_headers(url, timeout=5)
        self.assertFalse(result)

    @patch('requests.get')
    def test_coordinate_expansion_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        url = "http://example.com/expand"
        result = self.node.coordinate_expansion(url, timeout=5)
        self.assertTrue(result)
        mock_get.assert_called_once_with(url, timeout=5, stream=True)

    @patch('requests.get')
    def test_coordinate_expansion_failure(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 500
        mock_get.return_value = mock_response

        url = "http://example.com/error"
        result = self.node.coordinate_expansion(url, timeout=5)
        self.assertFalse(result)

    @patch('requests.get')
    def test_coordinate_expansion_safe_success(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        url = "http://example.com/safe"
        result = self.node.coordinate_expansion_safe(url, timeout=5)
        self.assertTrue(result)

    @patch('requests.get')
    def test_coordinate_expansion_safe_catches_exception(self, mock_get):
        mock_get.side_effect = requests.exceptions.ConnectionError("Connection failed")

        url = "http://example.com/unreachable"
        result = self.node.coordinate_expansion_safe(url, timeout=5)
        self.assertFalse(result)

    def test_export_and_get_exported_report(self):
        target = "http://target.com"
        report_data = {"status": "active", "nodes": 3}

        self.node.export_analytics_report(target, report_data)
        
        retrieved_report = self.node.get_exported_report(target)
        self.assertEqual(retrieved_report, report_data)

    @patch('requests.get')
    def test_process_stream(self, mock_get):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.iter_content.return_value = [b'chunk1', b'chunk2', b'chunk3']
        mock_get.return_value = mock_response

        url = "http://example.com/stream"
        try:
            self.node.process_stream(url, timeout=5)
        except Exception as e:
            self.fail(f"process_stream raised unexpected exception: {e}")

        mock_get.assert_called_once_with(url, timeout=5, stream=True)
        mock_response.iter_content.assert_called_once_with(chunk_size=8192)

if __name__ == '__main__':
    unittest.main()