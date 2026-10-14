import unittest
from unittest.mock import patch
import io
import random
import uuid
import requests

from skills.market_portfolio_stress_audit_health_monitor import (
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError,
    MarketPortfolioStressAuditHealthMonitor,
    _dummy_subsystem_func,
    __getattr__
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_name_1 = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.subsystem_name_2 = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.target_url = f"http://{uuid.uuid4().hex[:6]}.local/{uuid.uuid4().hex[:6]}"
        self.random_payload = uuid.uuid4().hex
        self.random_bytes = os_random_bytes = bytes(random.getrandbits(8) for _ in range(64))

    def test_init_default_subsystems(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(monitor.subsystems, [])

    def test_init_custom_subsystems(self):
        subsystems = [self.subsystem_name_1, self.subsystem_name_2]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)
        self.assertEqual(monitor.subsystems, subsystems)

    def test_probe_subsystem(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()
        result = monitor._probe_subsystem(self.subsystem_name_1)
        self.assertEqual(result["subsystem"], self.subsystem_name_1)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(result["token"])
        self.assertIsNone(result["error"])

    def test_run_full_audit_healthy(self):
        subsystems = [self.subsystem_name_1, self.subsystem_name_2]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)

        audit_result = monitor.run_full_audit()

        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn(self.subsystem_name_1, audit_result["subsystems_details"])
        self.assertIn(self.subsystem_name_2, audit_result["subsystems_details"])

    def test_run_full_audit_storage_unreachable_raises(self):
        subsystems = [self.subsystem_name_1]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)

        def mock_probe(name):
            raise StorageUnreachableError(uuid.uuid4().hex)

        with patch.object(monitor, '_probe_subsystem', side_effect=mock_probe):
            with self.assertRaises(StorageUnreachableError):
                monitor.run_full_audit()

    def test_run_full_audit_generic_exception_raises_execution_error(self):
        subsystems = [self.subsystem_name_1]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)
        error_message = uuid.uuid4().hex

        def mock_probe(name):
            raise RuntimeError(error_message)

        with patch.object(monitor, '_probe_subsystem', side_effect=mock_probe):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                monitor.run_full_audit()
            self.assertIn(error_message, str(ctx.exception))

    def test_run_full_audit_degraded_status(self):
        subsystems = [self.subsystem_name_1]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)

        def mock_probe(name):
            return {
                "subsystem": name,
                "status": SubsystemHealthStatus.DEGRADED,
                "token": None,
                "error": None
            }

        with patch.object(monitor, '_probe_subsystem', side_effect=mock_probe):
            audit_result = monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_unhealthy_status(self):
        subsystems = [self.subsystem_name_1]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subsystems)

        def mock_probe(name):
            return {
                "subsystem": name,
                "status": SubsystemHealthStatus.UNHEALTHY,
                "token": None,
                "error": None
            }

        with patch.object(monitor, '_probe_subsystem', side_effect=mock_probe):
            audit_result = monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)

    def test_verify_stream_pipeline_success(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()

        with patch('requests.get') as mock_get:
            mock_response = mock_get.return_value
            mock_response.content = self.random_bytes

            result = monitor.verify_stream_pipeline(self.target_url)

            mock_get.assert_called_once_with(self.target_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(self.random_bytes))

    def test_verify_stream_pipeline_failure(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()

        with patch('requests.get', side_effect=requests.RequestException(uuid.uuid4().hex)) as mock_get:
            result = monitor.verify_stream_pipeline(self.target_url)

            mock_get.assert_called_once_with(self.target_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_dummy_subsystem_func(self):
        res = _dummy_subsystem_func(self.random_payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["payload"], self.random_payload)

    def test_module_getattr(self):
        random_attr = uuid.uuid4().hex
        func = __getattr__(random_attr)
        self.assertTrue(callable(func))
        res = func(self.random_payload)
        self.assertEqual(res["payload"], self.random_payload)


if __name__ == '__main__':
    unittest.main()