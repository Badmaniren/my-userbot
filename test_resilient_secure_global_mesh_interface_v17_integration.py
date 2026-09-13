import unittest
from unittest.mock import patch, MagicMock
from skills.resilient_secure_global_mesh_interface_v17 import (
    ResilientSecureGlobalMeshInterfaceV17,
    ResilientSecureGlobalMeshInterfaceV17Error
)


class TestResilientSecureGlobalMeshInterfaceV17Integration(unittest.TestCase):

    def setUp(self):
        self.target_url = "http://example.com/mesh-target"
        self.report_payload = {"status": "operational", "nodes": 42}
        self.mesh_interface = ResilientSecureGlobalMeshInterfaceV17(
            db_path=":memory:",
            max_memory_mb=256,
            calls=50,
            period=1.0,
            raise_on_limit=True
        )

    @patch('requests.Session.get')
    @patch('requests.head')
    @patch('requests.get')
    def test_integration_flow(self, mock_get, mock_head, mock_session_get):
        mock_head_resp = MagicMock()
        mock_head_resp.status_code = 200
        mock_head.return_value = mock_head_resp

        mock_get_resp = MagicMock()
        mock_get_resp.status_code = 200
        mock_get_resp.text = "mesh stream payload data"
        mock_get_resp.content = b"mesh stream payload data"
        mock_get_resp.raw = MagicMock()
        mock_get_resp.raw.read.return_value = b"mesh stream payload data"
        mock_get.return_value = mock_get_resp
        mock_session_get.return_value = mock_get_resp

        self.assertTrue(self.mesh_interface.validate_target_headers(self.target_url, timeout=2))
        self.assertTrue(self.mesh_interface.coordinate_expansion(self.target_url, timeout=2))
        self.assertTrue(self.mesh_interface.coordinate_expansion_safe(self.target_url, timeout=2))

        self.mesh_interface.export_analytics_report(self.target_url, self.report_payload)
        retrieved_report = self.mesh_interface.get_exported_report(self.target_url)
        self.assertIsInstance(retrieved_report, dict)
        self.assertEqual(retrieved_report, self.report_payload)

        self.mesh_interface.process_stream(self.target_url, timeout=2)

        route_result = self.mesh_interface.route_request(self.target_url, timeout=2)
        self.assertIsNotNone(route_result)


if __name__ == '__main__':
    unittest.main()
