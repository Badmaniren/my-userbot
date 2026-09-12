import unittest
from unittest.mock import patch, MagicMock
import io

from skills.resilient_secure_smart_crawler_hub_v7_orchestrator import (
    ResilientSecureSmartCrawlerHubV7OrchestratorError,
    ResilientSecureSmartCrawlerHubV7Error,
    ResilientSecureSmartCrawlerHubV7,
    start_new
)


class TestResilientSecureSmartCrawlerHubV7Orchestrator(unittest.TestCase):

    def test_start_new_success(self):
        with patch.object(ResilientSecureSmartCrawlerHubV7, "process_stream", return_value={"status": "success"}) as mock_process:
            result = start_new("http://example.com", timeout=5)
            self.assertEqual(result, {"status": "success"})
            mock_process.assert_called_once_with("http://example.com", 5)

    def test_start_new_orchestrator_error(self):
        with patch.object(ResilientSecureSmartCrawlerHubV7, "process_stream", side_effect=Exception("Stream failure")):
            with self.assertRaises(ResilientSecureSmartCrawlerHubV7OrchestratorError) as ctx:
                start_new("http://example.com", timeout=5)
            self.assertIn("Stream failure", str(ctx.exception))

    def test_hub_init_defaults(self):
        hub = ResilientSecureSmartCrawlerHubV7()
        self.assertEqual(hub.db_path, ":memory:")
        self.assertEqual(hub.max_memory_mb, 128)
        self.assertEqual(hub.calls, 10)
        self.assertEqual(hub.period, 1.0)
        self.assertTrue(hub.raise_on_limit)

    def test_hub_validate_target_headers(self):
        hub = ResilientSecureSmartCrawlerHubV7()
        res = hub.validate_target_headers("http://example.com", 5)
        self.assertTrue(res)

    def test_hub_coordinate_expansion_safe(self):
        hub = ResilientSecureSmartCrawlerHubV7()
        res = hub.coordinate_expansion_safe("http://example.com", 5)
        self.assertTrue(res)

    def test_hub_coordinate_expansion_raises(self):
        hub = ResilientSecureSmartCrawlerHubV7()
        with self.assertRaises(ResilientSecureSmartCrawlerHubV7Error):
            hub.coordinate_expansion("http://example.com", 5)