import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
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
        self.random_subsystem_name = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.subsystems_list = [
            self.random_subsystem_name,
            f"vault_{uuid.uuid4().hex[:8]}",
            f"monitor_{uuid.uuid4().hex[:8]}"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.subsystems_list)

    def test_init_default_subsystems(self):
        monitor_default = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(monitor_default.subsystems, [])

    def test_init_custom_subsystems(self):
        self.assertEqual(self.monitor.subsystems, self.subsystems_list)

    def test_probe_subsystem_returns_expected_structure(self):
        probe_result = self.monitor._probe_subsystem(self.random_subsystem_name)
        self.assertIsInstance(probe_result, dict)
        self.assertEqual(probe_result["subsystem"], self.random_subsystem_name)
        self.assertEqual(probe_result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(probe_result["token"])
        self.assertIsNone(probe_result["error"])

    @patch('skills.market_portfolio_stress_audit_health_monitor.market_portfolio_stress_audit_summary_vault')
    def test_run_full_audit_all_healthy(self, mock_summary_vault):
        mock_summary_vault.fetch_summary = MagicMock(return_value={uuid.uuid4().hex: random.randint(1, 100)})

        result = self.monitor.run_full_audit()

        self.assertIn("global_status", result)
        self.assertIn("subsystems_details", result)
        self.assertEqual(result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertEqual(len(result["subsystems_details"]), len(self.subsystems_list))
        for sub in self.subsystems_list:
            self.assertEqual(result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    @patch('skills.market_portfolio_stress_audit_health_monitor.market_portfolio_stress_audit_summary_vault')
    def test_run_full_audit_with_degraded_status(self, mock_summary_vault):
        degraded_sub = self.subsystems_list[0]

        original_probe = self.monitor._probe_subsystem
        def custom_probe(name):
            res = original_probe(name)
            if name == degraded_sub:
                res["status"] = SubsystemHealthStatus.DEGRADED
            return res

        self.monitor._probe_subsystem = custom_probe

        result = self.monitor.run_full_audit()

        self.assertEqual(result["global_status"], SubsystemHealthStatus.DEGRADED)
        self.assertEqual(result["subsystems_details"][degraded_sub]["status"], SubsystemHealthStatus.DEGRADED)

    @patch('skills.market_portfolio_stress_audit_health_monitor.market_portfolio_stress_audit_summary_vault')
    def test_run_full_audit_with_unhealthy_status(self, mock_summary_vault):
        unhealthy_sub = self.subsystems_list[1]

        original_probe = self.monitor._probe_subsystem
        def custom_probe(name):
            res = original_probe(name)
            if name == unhealthy_sub:
                res["status"] = SubsystemHealthStatus.UNHEALTHY
            return res

        self.monitor._probe_subsystem = custom_probe

        result = self.monitor.run_full_audit()

        self.assertEqual(result["global_status"], SubsystemHealthStatus.UNHEALTHY)
        self.assertEqual(result["subsystems_details"][unhealthy_sub]["status"], SubsystemHealthStatus.UNHEALTHY)

    @patch('skills.market_portfolio_stress_audit_health_monitor.market_portfolio_stress_audit_summary_vault')
    def test_run_full_audit_storage_unreachable_exception(self, mock_summary_vault):
        original_probe = self.monitor._probe_subsystem
        def custom_probe(name):
            raise StorageUnreachableError(f"Vault unreachable for {name}")

        self.monitor._probe_subsystem = custom_probe

        with self.assertRaises(StorageUnreachableError):
            self.monitor.run_full_audit()

    @patch('skills.market_portfolio_stress_audit_health_monitor.market_portfolio_stress_audit_summary_vault')
    def test_run_full_audit_execution_error(self, mock_summary_vault):
        original_probe = self.monitor._probe_subsystem
        def custom_probe(name):
            raise RuntimeError(f"Unexpected failure in {name}")

        self.monitor._probe_subsystem = custom_probe

        with self.assertRaises(HealthMonitorExecutionError):
            self.monitor.run_full_audit()

    def test_verify_stream_pipeline_success(self):
        random_url = f"https://{uuid.uuid4().hex}.test/{uuid.uuid4().hex}"
        random_bytes_count = random.randint(10, 500)
        random_content = "".join(random.choices(string.ascii_letters, k=random_bytes_count)).encode('utf-8')

        with patch('skills.market_portfolio_stress_audit_health_monitor.requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = random_content
            mock_get.return_value = mock_response

            pipeline_result = self.monitor.verify_stream_pipeline(random_url)

            mock_get.assert_called_once_with(random_url)
            self.assertTrue(pipeline_result["is_active"])
            self.assertEqual(pipeline_result["bytes_read"], len(random_content))

    def test_verify_stream_pipeline_failure(self):
        random_url = f"https://{uuid.uuid4().hex}.test/{uuid.uuid4().hex}"

        with patch('skills.market_portfolio_stress_audit_health_monitor.requests.get') as mock_get:
            mock_get.side_effect = requests.exceptions.RequestException("Stream dead")

            pipeline_result = self.monitor.verify_stream_pipeline(random_url)

            mock_get.assert_called_once_with(random_url)
            self.assertFalse(pipeline_result["is_active"])
            self.assertEqual(pipeline_result["bytes_read"], 0)


if __name__ == '__main__':
    unittest.main()