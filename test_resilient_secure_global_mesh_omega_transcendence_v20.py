import unittest
from unittest.mock import patch, MagicMock
import io
import requests

from skills.resilient_secure_global_mesh_omega_transcendence_v20 import (
    ResilientSecureGlobalMeshOmegaTranscendenceV20,
    ResilientSecureGlobalMeshOmegaTranscendenceV20Error,
    ResilientSecureGlobalMeshomegaTranscendenceV20Error
)

class TestResilientSecureGlobalMeshOmegaTranscendenceV20(unittest.TestCase):

    def setUp(self):
        self.mesh = ResilientSecureGlobalMeshOmegaTranscendenceV20(
            db_path=":memory:",
            max_memory_mb=512,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_exceptions_compatibility(self):
        self.assertTrue(issubclass(ResilientSecureGlobalMeshomegaTranscendenceV20Error, Exception))
        self.assertEqual(
            ResilientSecureGlobalMeshOmegaTranscendenceV20Error,
            ResilientSecureGlobalMeshomegaTranscendenceV20Error
        )

    def test_validate_target_headers_success(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            res = self.mesh.validate_target_headers("http://example.com", 5)
            self.assertTrue(res)
            mock_head.assert_called_once_with("http://example.com", timeout=5)

    def test_validate_target_headers_failure(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response

            res = self.mesh.validate_target_headers("http://example.com", 5)
            self.assertFalse(res)

    def test_validate_target_headers_exception(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.head') as mock_head:
            mock_head.side_effect = requests.RequestException("Network error")

            res = self.mesh.validate_target_headers("http://example.com", 5)
            self.assertFalse(res)

    def test_coordinate_expansion_success(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            res = self.mesh.coordinate_expansion("http://example.com", 5)
            self.assertTrue(res)

    def test_coordinate_expansion_failure(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_get.return_value = mock_response

            res = self.mesh.coordinate_expansion("http://example.com", 5)
            self.assertFalse(res)

    def test_coordinate_expansion_safe_exception(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.get') as mock_get:
            mock_get.side_effect = OSError("Timeout")

            res = self.mesh.coordinate_expansion_safe("http://example.com", 5)
            self.assertFalse(res)

    def test_route_request(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.text = "transcendence payload"
            mock_get.return_value = mock_response

            res = self.mesh.route_request("http://example.com", 5)
            self.assertEqual(res, "transcendence payload")

    def test_process_stream(self):
        with patch('skills.resilient_secure_global_mesh_omega_transcendence_v20.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.iter_content.return_value = [b'chunk1', b'chunk2']
            mock_get.return_value = mock_response

            try:
                self.mesh.process_stream("http://example.com", 5)
            except Exception as e:
                self.fail(f"process_stream raised unexpected exception: {e}")

            mock_get.assert_called_once_with("http://example.com", timeout=5, stream=True)

    def test_export_and_get_exported_report(self):
        target = "http://node.local"
        report_data = {"status": "optimized", "metric": 99.9}

        self.mesh.export_analytics_report(target, report_data)
        exported = self.mesh.get_exported_report(target)

        self.assertEqual(exported, report_data)
        self.assertIsNot(exported, report_data) # Проверяем, что возвращается копия

    def test_get_exported_report_empty(self):
        exported = self.mesh.get_exported_report("http://unknown.local")
        self.assertEqual(exported, {})

if __name__ == '__main__':
    unittest.main()