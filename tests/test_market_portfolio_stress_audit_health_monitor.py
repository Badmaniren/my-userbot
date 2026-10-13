import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io

try:
    import requests
except ImportError:
    requests = None

from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError
)

class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.random_subsystems = [f"subsystem_{uuid.uuid4().hex[:8]}" for _ in range(random.randint(3, 7))]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.random_subsystems)

    def test_run_full_audit_integrity(self):
        # Интеграция с реальным Vault через мок, имитирующий структуру данных
        mock_vault_data = {sub: {"status": random.choice(list(SubsystemHealthStatus))} for sub in self.random_subsystems}

        with patch('skills.market_portfolio_stress_audit_health_monitor.market_portfolio_stress_audit_summary_vault') as mock_vault:
            mock_vault.get_all_statuses.return_value = mock_vault_data

            # Переопределяем метод пробы для использования реального Vault
            self.monitor._probe_subsystem = lambda name: mock_vault.get_all_statuses()[name]

            results = self.monitor.run_full_audit()

            self.assertIn("global_status", results)
            self.assertIn("subsystems_details", results)
            self.assertEqual(len(results["subsystems_details"]), len(self.random_subsystems))

            for sub in self.random_subsystems:
                self.assertEqual(results["subsystems_details"][sub], mock_vault_data[sub])

    def test_verify_stream_pipeline_success(self):
        target_url = f"http://{uuid.uuid4().hex}.com/{uuid.uuid4().hex}"
        random_bytes = uuid.uuid4().bytes

        with patch('skills.market_portfolio_stress_audit_health_monitor.requests') as mock_requests:
            if mock_requests is None:
                self.skipTest("requests library not available")
            mock_response = MagicMock()
            mock_response.content = random_bytes
            mock_requests.get.return_value = mock_response

            result = self.monitor.verify_stream_pipeline(target_url)

            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(random_bytes))
            mock_requests.get.assert_called_once_with(target_url)

    def test_verify_stream_pipeline_failure(self):
        target_url = f"http://{uuid.uuid4().hex}.internal"

        req_exception = getattr(requests, 'exceptions', None)
        exc = req_exception.RequestException if req_exception else Exception
        with patch('skills.market_portfolio_stress_audit_health_monitor.requests') as mock_requests:
            if mock_requests is None:
                self.skipTest("requests library not available")
            mock_requests.get.side_effect = exc
            result = self.monitor.verify_stream_pipeline(target_url)

            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_run_full_audit_exception_handling(self):
        failing_sub = self.random_subsystems[0]

        with patch.object(self.monitor, '_probe_subsystem', side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(HealthMonitorExecutionError):
                self.monitor.run_full_audit()

    def test_run_full_audit_storage_unreachable(self):
        with patch.object(self.monitor, '_probe_subsystem', side_effect=StorageUnreachableError):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

    def test_global_status_degradation_logic(self):
        # Проверка логики перехода статусов
        sub_healthy = "sub_h"
        sub_degraded = "sub_d"
        self.monitor.subsystems = [sub_healthy, sub_degraded]

        def side_effect(name):
            status = SubsystemHealthStatus.HEALTHY if name == sub_healthy else SubsystemHealthStatus.DEGRADED
            return {"status": status}

        with patch.object(self.monitor, '_probe_subsystem', side_effect=side_effect):
            result = self.monitor.run_full_audit()
            self.assertEqual(result["global_status"], SubsystemHealthStatus.DEGRADED)

if __name__ == '__main__':
    unittest.main()
