import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_global_mesh_router_v3 import (
    ResilientSecureGlobalMeshRouterV3,
    ResilientSecureGlobalMeshRouterV3Error,
)
from skills.resilient_secure_global_mesh_node_v2 import ResilientSecureGlobalMeshNodeV2
from skills.resilient_secure_smart_crawler_hub_v8_enterprise import ResilientSecureSmartCrawlerHubV8Enterprise


class TestResilientSecureGlobalMeshRouterV3(unittest.TestCase):

    def setUp(self):
        self.db_path = ":memory:"
        self.max_memory_mb = 512
        self.calls = 10
        self.period = 60
        self.raise_on_limit = True
        self.router = ResilientSecureGlobalMeshRouterV3(
            db_path=self.db_path,
            max_memory_mb=self.max_memory_mb,
            calls=self.calls,
            period=self.period,
            raise_on_limit=self.raise_on_limit
        )

    def test_initialization(self):
        self.assertIsInstance(self.router, ResilientSecureGlobalMeshRouterV3)
        self.assertIsInstance(self.router.mesh_node, ResilientSecureGlobalMeshNodeV2)
        self.assertIsInstance(self.router.crawler_hub, ResilientSecureSmartCrawlerHubV8Enterprise)

    def test_validate_target_headers_success(self):
        with patch('requests.head') as mock_head:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_head.return_value = mock_response

            result = self.router.validate_target_headers("https://example.com", timeout=5)
            self.assertTrue(result)

    def test_validate_target_headers_failure(self):
        with patch('requests.head') as mock_head:
            mock_head.side_effect = Exception("Connection error")

            result = self.router.validate_target_headers("https://example.com", timeout=5)
            self.assertFalse(result)

    def test_coordinate_expansion_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = io.BytesIO(b'{"status": "ok"}')
            mock_response.text = '{"status": "ok"}'
            mock_get.return_value = mock_response

            result = self.router.coordinate_expansion("https://example.com", timeout=5)
            self.assertTrue(result)

    def test_coordinate_expansion_safe_handles_exception(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Mesh expansion failure")

            result = self.router.coordinate_expansion_safe("https://example.com", timeout=5)
            self.assertFalse(result)

    def test_export_and_get_exported_report(self):
        target = "https://example.com/target"
        report_data = {"metric": 42, "status": "active"}

        self.router.export_analytics_report(target, report_data)
        report = self.router.get_exported_report(target)
        
        self.assertEqual(report, report_data)

    def test_process_stream_success(self):
        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = io.BytesIO(b'stream data payload')
            mock_response.iter_content.return_value = [b'stream data payload']
            mock_get.return_value = mock_response

            try:
                self.router.process_stream("https://example.com/stream", timeout=5)
            except Exception as e:
                self.fail(f"process_stream raised unexpected exception: {e}")

    def test_process_stream_failure_raises_error(self):
        with patch('requests.get') as mock_get:
            mock_get.side_effect = Exception("Stream error")

            with self.assertRaises((ResilientSecureGlobalMeshRouterV3Error, Exception)):
                self.router.process_stream("https://example.com/stream", timeout=5)


if __name__ == '__main__':
    unittest.main()