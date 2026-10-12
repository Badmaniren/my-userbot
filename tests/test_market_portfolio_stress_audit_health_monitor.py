import unittest
from unittest.mock import patch
import random
import uuid
import string
import requests
import io

from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError
)

class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_name = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name])

    def test_init_default_subsystems(self):
        random_sub = f"sub_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(monitor.subsystems, [])

    def test_probe_subsystem_returns_structure(self):
        res = self.monitor._probe_subsystem(self.subsystem_name)
        self.assertIn("subsystem", res)
        self.assertIn("status", res)
        self.assertEqual(res["subsystem"], self.subsystem_name)
        self.assertEqual(res["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_healthy(self):
        audit_result = self.monitor.run_full_audit()
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn(self.subsystem_name, audit_result["subsystems_details"])

    def test_run_full_audit_storage_unreachable_exception(self):
        faulty_sub = f"faulty_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[faulty_sub])

        with patch.object(monitor, '_probe_subsystem', side_effect=StorageUnreachableError(uuid.uuid4().hex)):
            with self.assertRaises(StorageUnreachableError):
                monitor.run_full_audit()

    def test_run_full_audit_execution_error_exception(self):
        faulty_sub = f"faulty_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[faulty_sub])
        random_error_msg = uuid.uuid4().hex

        with patch.object(monitor, '_probe_subsystem', side_effect=ValueError(random_error_msg)):
            with self.assertRaises(HealthMonitorExecutionError):
                monitor.run_full_audit()

    def test_run_full_audit_degraded_status(self):
        deg_sub = f"deg_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[deg_sub])
        random_token = uuid.uuid4().hex

        mock_result = {
            "subsystem": deg_sub,
            "status": SubsystemHealthStatus.DEGRADED,
            "token": random_token,
            "error": None
        }

        with patch.object(monitor, '_probe_subsystem', return_value=mock_result):
            res = monitor.run_full_audit()
            self.assertEqual(res["global_status"], SubsystemHealthStatus.DEGRADED)
            self.assertEqual(res["subsystems_details"][deg_sub]["token"], random_token)

    def test_run_full_audit_unhealthy_status(self):
        un_sub = f"un_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[un_sub])
        random_err = uuid.uuid4().hex

        mock_result = {
            "subsystem": un_sub,
            "status": SubsystemHealthStatus.UNHEALTHY,
            "token": None,
            "error": random_err
        }

        with patch.object(monitor, '_probe_subsystem', return_value=mock_result):
            res = monitor.run_full_audit()
            self.assertEqual(res["global_status"], SubsystemHealthStatus.UNHEALTHY)
            self.assertEqual(res["subsystems_details"][un_sub]["error"], random_err)

    def test_verify_stream_pipeline_success(self):
        target_url = f"http://{uuid.uuid4().hex[:8]}.local/stream"
        random_bytes_count = random.randint(10, 256)
        random_content = bytes(random.choices(range(256), k=random_bytes_count))

        class MockResponse:
            content = random_content

        with patch('requests.get', return_value=MockResponse()) as mock_get:
            result = self.monitor.verify_stream_pipeline(target_url)
            mock_get.assert_called_once_with(target_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], random_bytes_count)

    def test_verify_stream_pipeline_failure(self):
        target_url = f"http://{uuid.uuid4().hex[:8]}.local/fail"
        random_err_msg = uuid.uuid4().hex

        with patch('requests.get', side_effect=requests.RequestException(random_err_msg)):
            result = self.monitor.verify_stream_pipeline(target_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_dynamic_attributes_fallback(self):
        import skills.market_portfolio_stress_audit_health_monitor as monitor_module
        random_attr = f"subsystem_agent_{uuid.uuid4().hex[:6]}"
        attr_func = getattr(monitor_module, random_attr, None)
        self.assertIsNotNone(attr_func)
        random_payload = uuid.uuid4().hex
        call_res = attr_func(random_payload)
        self.assertEqual(call_res["status"], "ok")
        self.assertEqual(call_res["payload"], random_payload)

    def test_stream_ingestor_and_sink_verification(self):
        target_url = f"https://{uuid.uuid4().hex[:10]}.org/ingest"
        alphabet_bytes = string.ascii_letters.encode('ascii') + string.digits.encode('ascii')
        random_payload = b"".join(random.choices([bytes([b]) for b in alphabet_bytes], k=128))

        class MockResponseStream:
            content = random_payload

        with patch('requests.get', return_value=MockResponseStream()) as mock_req:
            res = self.monitor.verify_stream_pipeline(target_url)
            mock_req.assert_called_once_with(target_url)
            self.assertTrue(res["is_active"])
            self.assertEqual(res["bytes_read"], len(random_payload))

if __name__ == '__main__':
    unittest.main()