import unittest
from unittest.mock import patch, MagicMock
import requests
import io
from skills.resilient_secure_global_mesh_coordinator_v4 import (
    ResilientSecureGlobalMeshCoordinatorV4,
    ResilientSecureGlobalMeshCoordinatorV4Error
)

class TestResilientSecureGlobalMeshCoordinatorV4(unittest.TestCase):
    def setUp(self):
        self.coordinator = ResilientSecureGlobalMeshCoordinatorV4(
            db_path=":memory:",
            max_memory_mb=128,
            calls=5,
            period=1.0,
            raise_on_limit=True
        )

    def test_validate_target_headers_success(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            res = self.coordinator.validate_target_headers("https://example.com", 5)
            self.assertTrue(res)

    def test_validate_target_headers_failure(self):
        with patch('requests.head') as mock_head:
            mock_head.side_effect = requests.RequestException("Connection error")

            res = self.coordinator.validate_target_headers("https://example.com", 5)
            self.assertFalse(res)

    def test_coordinate_expansion_delegation(self):
        with patch.object(self.coordinator.router, 'coordinate_expansion') as mock_coord:
            mock_coord.return_value = True
            res = self.coordinator.coordinate_expansion("https://example.com", 5)
            self.assertTrue(res)
            mock_coord.assert_called_once_with("https://example.com", 5)

    def test_coordinate_expansion_safe_handling(self):
        with patch.object(self.coordinator.router, 'coordinate_expansion') as mock_coord:
            mock_coord.side_effect = Exception("Router failure")
            res = self.coordinator.coordinate_expansion_safe("https://example.com", 5)
            self.assertFalse(res)

    def test_analytics_report_storage(self):
        data = {"status": "ok", "nodes": 3}
        self.coordinator.export_analytics_report("target_node", data)
        report = self.coordinator.get_exported_report("target_node")
        self.assertEqual(report, data)
        self.assertIsNot(report, data)

    def test_process_stream(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
            mock_get.return_value = mock_response

            res = self.coordinator.process_stream("https://example.com", 5)
            self.assertIsNone(res)
            mock_get.assert_called_once()

    def test_raise_on_limit_behavior(self):
        self.coordinator.raise_on_limit = True
        with patch.object(self.coordinator.router, 'coordinate_expansion') as mock_coord:
            mock_coord.side_effect = Exception("Limit reached")
            with self.assertRaises(ResilientSecureGlobalMeshCoordinatorV4Error):
                self.coordinator.coordinate_expansion("https://example.com", 5)

if __name__ == '__main__':
    unittest.main()