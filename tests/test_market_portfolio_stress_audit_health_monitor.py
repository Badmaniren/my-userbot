import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
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
        self.random_subsystem_name = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.random_subsystem_list = [
            f"sub_{uuid.uuid4().hex[:6]}",
            f"sub_{uuid.uuid4().hex[:6]}"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.random_subsystem_list)

    def test_init_default_subsystems(self):
        default_monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(default_monitor.subsystems, [])

    def test_init_custom_subsystems(self):
        custom_subs = [f"mod_{uuid.uuid4().hex[:5]}" for _ in range(3)]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=custom_subs)
        self.assertEqual(monitor.subsystems, custom_subs)

    def test_probe_subsystem_returns_expected_structure(self):
        result = self.monitor._probe_subsystem(self.random_subsystem_name)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["subsystem"], self.random_subsystem_name)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(result["token"])
        self.assertIsNone(result["error"])

    def test_run_full_audit_all_healthy(self):
        audit_result = self.monitor.run_full_audit()
        self.assertIn("global_status", audit_result)
        self.assertIn("subsystems_details", audit_result)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertEqual(len(audit_result["subsystems_details"]), len(self.random_subsystem_list))
        for sub in self.random_subsystem_list:
            self.assertIn(sub, audit_result["subsystems_details"])
            self.assertEqual(audit_result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_with_degraded_status(self):
        degraded_sub = self.random_subsystem_list[0]

        def mock_probe(name):
            res = {
                "subsystem": name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }
            if name == degraded_sub:
                res["status"] = SubsystemHealthStatus.DEGRADED
            return res

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)
            self.assertEqual(audit_result["subsystems_details"][degraded_sub]["status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_with_unhealthy_status(self):
        unhealthy_sub = self.random_subsystem_list[1]

        def mock_probe(name):
            res = {
                "subsystem": name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }
            if name == unhealthy_sub:
                res["status"] = SubsystemHealthStatus.UNHEALTHY
            return res

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)
            self.assertEqual(audit_result["subsystems_details"][unhealthy_sub]["status"], SubsystemHealthStatus.UNHEALTHY)

    def test_run_full_audit_raises_storage_unreachable_error(self):
        def mock_probe(name):
            raise StorageUnreachableError(f"Storage down for {name}")

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

    def test_run_full_audit_raises_health_monitor_execution_error(self):
        random_err_msg = f"error_{uuid.uuid4().hex}"
        def mock_probe(name):
            raise RuntimeError(random_err_msg)

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                self.monitor.run_full_audit()
            self.assertIn(random_err_msg, str(ctx.exception))

    def test_verify_stream_pipeline_success(self):
        random_url = f"http://{uuid.uuid4().hex}.local/stream"
        random_bytes = f"payload_{uuid.uuid4().hex}".encode('utf-8')

        mock_response = MagicMock()
        mock_response.content = random_bytes

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_verify_stream_pipeline_failure(self):
        random_url = f"http://{uuid.uuid4().hex}.local/stream"

        with patch('requests.get', side_effect=requests.exceptions.RequestException("Connection refused")):
            result = self.monitor.verify_stream_pipeline(random_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_dummy_subsystem_func(self):
        random_payload = {"data": uuid.uuid4().hex}
        res = _dummy_subsystem_func(random_payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["payload"], random_payload)

    def test_module_getattr(self):
        random_attr = f"unknown_{uuid.uuid4().hex}"
        attr = __getattr__(random_attr)
        self.assertTrue(callable(attr))
        random_payload = uuid.uuid4().hex
        res = attr(random_payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["payload"], random_payload)


if __name__ == '__main__':
    unittest.main()