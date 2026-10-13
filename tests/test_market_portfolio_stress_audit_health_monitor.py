import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import requests

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
        monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(monitor.subsystems, [])

    def test_init_custom_subsystems(self):
        sub_list = [f"sub_{uuid.uuid4().hex[:6]}" for _ in range(3)]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=sub_list)
        self.assertEqual(monitor.subsystems, sub_list)

    def test_probe_subsystem(self):
        result = self.monitor._probe_subsystem(self.subsystem_name)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["subsystem"], self.subsystem_name)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn("token", result)
        self.assertIn("error", result)

    def test_run_full_audit_healthy(self):
        audit_result = self.monitor.run_full_audit()
        self.assertIsInstance(audit_result, dict)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn(self.subsystem_name, audit_result["subsystems_details"])
        sub_detail = audit_result["subsystems_details"][self.subsystem_name]
        self.assertEqual(sub_detail["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_degraded(self):
        sub_deg = f"deg_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[sub_deg])

        with patch.object(monitor, '_probe_subsystem', return_value={
            "subsystem": sub_deg,
            "status": SubsystemHealthStatus.DEGRADED,
            "token": None,
            "error": None
        }):
            res = monitor.run_full_audit()
            self.assertEqual(res["global_status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_unhealthy(self):
        sub_unh = f"unh_{uuid.uuid4().hex[:6]}"
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name, sub_unh])

        def mock_probe(name):
            if name == sub_unh:
                return {
                    "subsystem": name,
                    "status": SubsystemHealthStatus.UNHEALTHY,
                    "token": None,
                    "error": "Critical Failure"
                }
            return {
                "subsystem": name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }

        with patch.object(monitor, '_probe_subsystem', side_effect=mock_probe):
            res = monitor.run_full_audit()
            self.assertEqual(res["global_status"], SubsystemHealthStatus.UNHEALTHY)

    def test_run_full_audit_storage_unreachable_exception(self):
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name])

        with patch.object(monitor, '_probe_subsystem', side_effect=StorageUnreachableError):
            with self.assertRaises(StorageUnreachableError):
                monitor.run_full_audit()

    def test_run_full_audit_generic_exception(self):
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name])
        err_msg = f"err_{uuid.uuid4().hex[:6]}"

        with patch.object(monitor, '_probe_subsystem', side_effect=Exception(err_msg)):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                monitor.run_full_audit()
            self.assertIn(err_msg, str(ctx.exception))

    def test_verify_stream_pipeline_success(self):
        target_url = f"http://{uuid.uuid4().hex[:8]}.local/stream"
        random_payload = f"payload_{uuid.uuid4().hex}".encode('utf-8')

        mock_response = MagicMock()
        mock_response.content = random_payload

        with patch('requests.get', return_value=mock_response) as mock_get:
            res = self.monitor.verify_stream_pipeline(target_url)
            mock_get.assert_called_once_with(target_url)
            self.assertTrue(res["is_active"])
            self.assertEqual(res["bytes_read"], len(random_payload))

    def test_verify_stream_pipeline_failure(self):
        target_url = f"http://{uuid.uuid4().hex[:8]}.local/fail"

        with patch('requests.get', side_effect=requests.RequestException("Connection error")):
            res = self.monitor.verify_stream_pipeline(target_url)
            self.assertFalse(res["is_active"])
            self.assertEqual(res["bytes_read"], 0)


if __name__ == '__main__':
    unittest.main()