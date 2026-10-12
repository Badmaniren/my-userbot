import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import requests

from skills.market_portfolio_stress_audit_health_monitor import (
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError,
    MarketPortfolioStressAuditHealthMonitor
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_count = random.randint(1, 5)
        self.subsystems = [f"subsystem_{uuid.uuid4().hex[:8]}" for _ in range(self.subsystem_count)]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.subsystems)

    def test_init_default_subsystems(self):
        default_monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(default_monitor.subsystems, [])

    def test_run_full_audit_healthy(self):
        audit_result = self.monitor.run_full_audit()
        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertEqual(len(audit_result["subsystems_details"]), self.subsystem_count)
        for sub in self.subsystems:
            self.assertIn(sub, audit_result["subsystems_details"])
            self.assertEqual(audit_result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_storage_unreachable_exception(self):
        target_sub = random.choice(self.subsystems)
        error_msg = uuid.uuid4().hex

        def side_effect(sub_name):
            if sub_name == target_sub:
                raise StorageUnreachableError(error_msg)
            return {
                "subsystem": sub_name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=side_effect):
            with self.assertRaises(StorageUnreachableError) as ctx:
                self.monitor.run_full_audit()
            self.assertEqual(str(ctx.exception), error_msg)

    def test_run_full_audit_execution_error_exception(self):
        target_sub = random.choice(self.subsystems)
        error_msg = uuid.uuid4().hex

        def side_effect(sub_name):
            if sub_name == target_sub:
                raise ValueError(error_msg)
            return {
                "subsystem": sub_name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=side_effect):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                self.monitor.run_full_audit()
            self.assertIn(error_msg, str(ctx.exception))

    def test_run_full_audit_status_aggregation_degraded(self):
        degraded_sub = random.choice(self.subsystems)

        def side_effect(sub_name):
            status = SubsystemHealthStatus.DEGRADED if sub_name == degraded_sub else SubsystemHealthStatus.HEALTHY
            return {
                "subsystem": sub_name,
                "status": status,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=side_effect):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)
            self.assertEqual(audit_result["subsystems_details"][degraded_sub]["status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_status_aggregation_unhealthy(self):
        unhealthy_sub = random.choice(self.subsystems)

        def side_effect(sub_name):
            status = SubsystemHealthStatus.UNHEALTHY if sub_name == unhealthy_sub else SubsystemHealthStatus.HEALTHY
            return {
                "subsystem": sub_name,
                "status": status,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=side_effect):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)
            self.assertEqual(audit_result["subsystems_details"][unhealthy_sub]["status"], SubsystemHealthStatus.UNHEALTHY)

    def test_verify_stream_pipeline_success(self):
        random_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=10))}.local/{uuid.uuid4().hex}"
        random_bytes_data = uuid.uuid4().bytes + ''.join(random.choices(string.ascii_letters, k=50)).encode('utf-8')
        expected_length = len(random_bytes_data)

        mock_response = MagicMock()
        mock_response.content = random_bytes_data

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], expected_length)

    def test_verify_stream_pipeline_failure(self):
        random_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=10))}.local/{uuid.uuid4().hex}"
        error_msg = uuid.uuid4().hex

        with patch('requests.get', side_effect=requests.exceptions.RequestException(error_msg)) as mock_get:
            result = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)


if __name__ == '__main__':
    unittest.main()