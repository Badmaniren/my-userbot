import unittest
from unittest.mock import patch, MagicMock
import io
import requests

from skills.resilient_secure_global_mesh_omega_hive_v15 import (
    ResilientSecureGlobalMeshOmegaHiveV15,
    ResilientSecureGlobalMeshOmegaHiveV15Error
)


class TestResilientSecureGlobalMeshOmegaHiveV15(unittest.TestCase):

    def setUp(self):
        self.hive = ResilientSecureGlobalMeshOmegaHiveV15(
            db_path=":memory:",
            max_memory_mb=100,
            calls=10,
            period=1.0,
            raise_on_limit=True
        )

    def test_initialization(self):
        self.assertEqual(self.hive.db_path, ":memory:")
        self.assertEqual(self.hive.max_memory_mb, 100)
        self.assertEqual(self.hive.calls, 10)
        self.assertEqual(self.hive.period, 1.0)
        self.assertTrue(self.hive.raise_on_limit)
        self.assertIsInstance(self.hive.reports, dict)

    def test_validate_target_headers_success(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            result = self.hive.validate_target_headers("http://example.com")
            self.assertTrue(result)
            mock_head.assert_called_once()

    def test_validate_target_headers_failure(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 404
            mock_head.return_value = mock_response

            result = self.hive.validate_target_headers("http://example.com")
            self.assertFalse(result)

    def test_validate_target_headers_exception(self):
        with patch('requests.head', side_effect=requests.RequestException):
            result = self.hive.validate_target_headers("http://example.com")
            self.assertFalse(result)

    def test_coordinate_expansion_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = self.hive.coordinate_expansion("http://example.com")
            self.assertTrue(result)
            mock_get.assert_called_once()

    def test_coordinate_expansion_safe_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            result = self.hive.coordinate_expansion_safe("http://example.com")
            self.assertTrue(result)

    def test_coordinate_expansion_safe_exception(self):
        with patch('requests.get', side_effect=requests.RequestException):
            result = self.hive.coordinate_expansion_safe("http://example.com")
            self.assertFalse(result)

    def test_export_and_get_exported_report(self):
        target = "http://node-omega.local"
        report_data = {"status": "active", "nodes": 100}

        self.hive.export_analytics_report(target, report_data)
        fetched_report = self.hive.get_exported_report(target)

        self.assertEqual(fetched_report, report_data)
        self.assertIsNot(fetched_report, report_data)  # Проверка возврата копии словаря

    def test_get_exported_report_empty(self):
        fetched = self.hive.get_exported_report("http://nonexistent.local")
        self.assertEqual(fetched, {})

    def test_process_stream(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.raw = io.BytesIO(b"stream_data_omega_v15")
            mock_get.return_value = mock_response

            try:
                self.hive.process_stream("http://example.com/stream")
            except Exception as e:
                self.fail(f"process_stream raised unexpected exception: {e}")

            mock_get.assert_called_once()

    def test_route_request(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_get.return_value = mock_response

            response = self.hive.route_request("http://example.com/route")
            self.assertEqual(response.status_code, 200)
            mock_get.assert_called_once()

    def test_custom_exception(self):
        with self.assertRaises(ResilientSecureGlobalMeshOmegaHiveV15Error):
            raise ResilientSecureGlobalMeshOmegaHiveV15Error("Omega Hive critical anomaly")


if __name__ == '__main__':
    unittest.main()