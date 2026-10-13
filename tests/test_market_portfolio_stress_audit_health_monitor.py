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
        self.random_subsystems = [f"subsystem_{uuid.uuid4().hex[:8]}" for _ in range(random.randint(3, 7))]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.random_subsystems)

    def test_run_full_audit_integrity(self):
        # Проверка, что монитор корректно агрегирует статусы без хардкода
        with patch.object(MarketPortfolioStressAuditHealthMonitor, '_probe_subsystem') as mock_probe:
            target_sub = random.choice(self.random_subsystems)
            mock_probe.return_value = {
                "subsystem": target_sub,
                "status": SubsystemHealthStatus.UNHEALTHY,
                "token": uuid.uuid4().hex,
                "error": "critical_failure"
            }

            result = self.monitor.run_full_audit()

            self.assertEqual(result["global_status"], SubsystemHealthStatus.UNHEALTHY)
            self.assertIn(target_sub, result["subsystems_details"])
            self.assertEqual(result["subsystems_details"][target_sub]["error"], "critical_failure")

    def test_run_full_audit_exception_handling(self):
        # Проверка проброса исключений при сбое хранилища
        with patch.object(MarketPortfolioStressAuditHealthMonitor, '_probe_subsystem', side_effect=StorageUnreachableError):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

        # Проверка обертки в HealthMonitorExecutionError
        with patch.object(MarketPortfolioStressAuditHealthMonitor, '_probe_subsystem', side_effect=Exception("random_crash")):
            with self.assertRaises(HealthMonitorExecutionError):
                self.monitor.run_full_audit()

    def test_verify_stream_pipeline_success(self):
        # Проверка чтения потока с генерацией случайного контента
        target_url = f"http://{uuid.uuid4().hex}.com/stream"
        random_bytes = bytes([random.randint(0, 255) for _ in range(64)])

        with patch('requests.get') as mock_get:
            mock_response = MagicMock()
            mock_response.content = random_bytes
            mock_get.return_value = mock_response

            result = self.monitor.verify_stream_pipeline(target_url)

            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(random_bytes))
            mock_get.assert_called_once_with(target_url)

    def test_verify_stream_pipeline_failure(self):
        # Проверка поведения при недоступности внешнего ресурса
        target_url = f"http://{uuid.uuid4().hex}.internal/fail"

        with patch('requests.get', side_effect=requests.exceptions.RequestException):
            result = self.monitor.verify_stream_pipeline(target_url)

            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_global_status_degradation_logic(self):
        # Проверка логики перехода в DEGRADED при наличии хотя бы одного деградировавшего узла
        with patch.object(MarketPortfolioStressAuditHealthMonitor, '_probe_subsystem') as mock_probe:
            def side_effect(name):
                return {
                    "subsystem": name,
                    "status": SubsystemHealthStatus.DEGRADED if name == self.random_subsystems[0] else SubsystemHealthStatus.HEALTHY,
                    "token": None,
                    "error": None
                }

            mock_probe.side_effect = side_effect
            result = self.monitor.run_full_audit()

            self.assertEqual(result["global_status"], SubsystemHealthStatus.DEGRADED)

if __name__ == '__main__':
    unittest.main()