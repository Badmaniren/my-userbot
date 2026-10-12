import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
import requests

from skills.market_portfolio_stress_audit_health_monitor import (
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError,
    MarketPortfolioStressAuditHealthMonitor
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_name = uuid.uuid4().hex
        self.monitor = MarketPortfolioStressAuditHealthMonitor([self.subsystem_name])

    def test_subsystem_health_status_enum_values(self):
        random_suffix = uuid.uuid4().hex[:6]
        healthy_val = f"HEALTHY_{random_suffix}"
        degraded_val = f"DEGRADED_{random_suffix}"
        unhealthy_val = f"UNHEALTHY_{random_suffix}"

        self.assertEqual(SubsystemHealthStatus.HEALTHY.value, "HEALTHY")
        self.assertEqual(SubsystemHealthStatus.DEGRADED.value, "DEGRADED")
        self.assertEqual(SubsystemHealthStatus.UNHEALTHY.value, "UNHEALTHY")

    def test_probe_subsystem_structure(self):
        random_sub = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor([random_sub])
        result = monitor._probe_subsystem(random_sub)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["subsystem"], random_sub)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(result["token"])
        self.assertIsNone(result["error"])

    def test_run_full_audit_healthy(self):
        subs = [uuid.uuid4().hex for _ in range(random.randint(1, 5))]
        monitor = MarketPortfolioStressAuditHealthMonitor(subs)
        audit_result = monitor.run_full_audit()

        self.assertIsInstance(audit_result, dict)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertEqual(len(audit_result["subsystems_details"]), len(subs))

        for sub in subs:
            self.assertIn(sub, audit_result["subsystems_details"])
            self.assertEqual(audit_result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_degraded_propagation(self):
        sub_healthy = uuid.uuid4().hex
        sub_degraded = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor([sub_healthy, sub_degraded])

        def custom_probe(name):
            status = SubsystemHealthStatus.DEGRADED if name == sub_degraded else SubsystemHealthStatus.HEALTHY
            return {
                "subsystem": name,
                "status": status,
                "token": uuid.uuid4().hex,
                "error": None
            }

        with patch.object(monitor, '_probe_subsystem', side_effect=custom_probe):
            audit_result = monitor.run_full_audit()

        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)
        self.assertEqual(audit_result["subsystems_details"][sub_degraded]["status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_unhealthy_propagation(self):
        sub_healthy = uuid.uuid4().hex
        sub_unhealthy = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor([sub_healthy, sub_unhealthy])

        def custom_probe(name):
            status = SubsystemHealthStatus.UNHEALTHY if name == sub_unhealthy else SubsystemHealthStatus.HEALTHY
            return {
                "subsystem": name,
                "status": status,
                "token": None,
                "error": uuid.uuid4().hex
            }

        with patch.object(monitor, '_probe_subsystem', side_effect=custom_probe):
            audit_result = monitor.run_full_audit()

        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)
        self.assertEqual(audit_result["subsystems_details"][sub_unhealthy]["status"], SubsystemHealthStatus.UNHEALTHY)

    def test_run_full_audit_storage_unreachable_exception(self):
        sub_name = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor([sub_name])

        with patch.object(monitor, '_probe_subsystem', side_effect=StorageUnreachableError(uuid.uuid4().hex)):
            with self.assertRaises(StorageUnreachableError):
                monitor.run_full_audit()

    def test_run_full_audit_execution_error_wrapping(self):
        sub_name = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor([sub_name])
        random_error_msg = uuid.uuid4().hex

        with patch.object(monitor, '_probe_subsystem', side_effect=RuntimeError(random_error_msg)):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                monitor.run_full_audit()
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_verify_stream_pipeline_success(self):
        target_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"
        random_bytes_count = random.randint(10, 500)
        random_content = bytes(random.choices(range(256), k=random_bytes_count))

        mock_response = MagicMock()
        mock_response.content = random_content

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.monitor.verify_stream_pipeline(target_url)

            mock_get.assert_called_once_with(target_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], random_bytes_count)

    def test_verify_stream_pipeline_failure(self):
        target_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=10))}.com/{uuid.uuid4().hex}"
        error_msg = uuid.uuid4().hex

        with patch('requests.get', side_effect=requests.RequestException(error_msg)) as mock_get:
            result = self.monitor.verify_stream_pipeline(target_url)

            mock_get.assert_called_once_with(target_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)


if __name__ == '__main__':
    unittest.main()