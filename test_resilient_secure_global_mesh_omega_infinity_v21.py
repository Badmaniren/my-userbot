import unittest
from unittest.mock import patch
import io

from skills.resilient_secure_global_mesh_omega_infinity_v21 import (
    ResilientSecureGlobalMeshOmegaInfinityV21,
    ResilientSecureGlobalMeshOmegaInfinityV21Error
)
from skills import resilient_secure_global_mesh_omega_transcendence_v20
from skills import resilient_secure_global_mesh_interface_v17


class TestResilientSecureGlobalMeshOmegaInfinityV21(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 1.0
        self.raise_on_limit = True
        self.target = "https://example.com"
        self.timeout = 5
        
        self.node = ResilientSecureGlobalMeshOmegaInfinityV21(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_composition_modules_present(self):
        self.assertIsNotNone(resilient_secure_global_mesh_omega_transcendence_v20)
        self.assertIsNotNone(resilient_secure_global_mesh_interface_v17)

    def test_validate_target_headers_success(self):
        with patch("requests.head") as mock_head:
            mock_head.return_value.status_code = 200
            res = self.node.validate_target_headers(self.target, self.timeout)
            self.assertTrue(res)

    def test_validate_target_headers_failure(self):
        with patch("requests.head") as mock_head:
            mock_head.side_effect = Exception("Connection error")
            res = self.node.validate_target_headers(self.target, self.timeout)
            self.assertFalse(res)

    def test_coordinate_expansion_success(self):
        with patch("requests.head") as mock_head:
            mock_head.return_value.status_code = 200
            res = self.node.coordinate_expansion(self.target, self.timeout)
            self.assertTrue(res)

    def test_coordinate_expansion_safe(self):
        with patch("requests.head") as mock_head:
            mock_head.side_effect = Exception("Expansion failure")
            res = self.node.coordinate_expansion_safe(self.target, self.timeout)
            self.assertFalse(res)

    def test_route_request(self):
        with patch("requests.get") as mock_get:
            mock_get.return_value.status_code = 200
            mock_get.return_value.text = "Transcendental Singularity Flow"
            res = self.node.route_request(self.target, self.timeout)
            self.assertIsInstance(res, str)

    def test_process_stream(self):
        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.status_code = 200
            mock_response.iter_content.return_value = [b"chunk1", b"chunk2"]
            try:
                self.node.process_stream(self.target, self.timeout)
            except Exception as e:
                self.fail(f"process_stream raised unexpected exception: {e}")

    def test_export_and_get_exported_report(self):
        report_data = {"singularity": "omega_infinity_v21", "status": "active"}
        self.node.export_analytics_report(self.target, report_data)
        report = self.node.get_exported_report(self.target)
        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("status"), "active")

    def test_custom_exception(self):
        with self.assertRaises(ResilientSecureGlobalMeshOmegaInfinityV21Error):
            raise ResilientSecureGlobalMeshOmegaInfinityV21Error("Singularity collapse error")


if __name__ == "__main__":
    unittest.main()