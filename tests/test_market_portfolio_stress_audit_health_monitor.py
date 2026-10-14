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
    __getattr__
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def test_subsystem_health_status_enum_values(self):
        rand_val = random.choice(list(SubsystemHealthStatus))
        self.assertIn(rand_val.value, ["HEALTHY", "DEGRADED", "UNHEALTHY"])

    def test_monitor_initialization(self):
        rand_subsystems = [uuid.uuid4().hex for _ in range(random.randint(1, 5))]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=rand_subsystems)
        self.assertEqual(monitor.subsystems, rand_subsystems)

        empty_monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(empty_monitor.subsystems, [])

    def test_run_full_audit_healthy(self):
        rand_subsystems = [uuid.uuid4().hex for _ in range(random.randint(2, 4))]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=rand_subsystems)

        with patch.object(monitor, '_probe_subsystem') as mock_probe:
            mock_probe.side_effect = lambda name: {
                "subsystem": name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": uuid.uuid4().hex,
                "error": None
            }

            audit_result = monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
            self.assertEqual(len(audit_result["subsystems_details"]), len(rand_subsystems))
            for sub in rand_subsystems:
                self.assertIn(sub, audit_result["subsystems_details"])
                self.assertEqual(audit_result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_storage_unreachable_exception(self):
        rand_sub = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[rand_sub])

        with patch.object(monitor, '_probe_subsystem') as mock_probe:
            mock_probe.side_effect = StorageUnreachableError(uuid.uuid4().hex)
            with self.assertRaises(StorageUnreachableError):
                monitor.run_full_audit()

    def test_run_full_audit_execution_error_exception(self):
        rand_sub = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[rand_sub])
        rand_error_msg = uuid.uuid4().hex

        with patch.object(monitor, '_probe_subsystem') as mock_probe:
            mock_probe.side_effect = RuntimeError(rand_error_msg)
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                monitor.run_full_audit()
            self.assertIn(rand_error_msg, str(ctx.exception))

    def test_run_full_audit_degraded_status(self):
        sub_healthy = uuid.uuid4().hex
        sub_degraded = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[sub_healthy, sub_degraded])

        with patch.object(monitor, '_probe_subsystem') as mock_probe:
            def side_effect_func(name):
                status = SubsystemHealthStatus.DEGRADED if name == sub_degraded else SubsystemHealthStatus.HEALTHY
                return {
                    "subsystem": name,
                    "status": status,
                    "token": None,
                    "error": uuid.uuid4().hex
                }
            mock_probe.side_effect = side_effect_func

            audit_result = monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_unhealthy_status(self):
        sub_healthy = uuid.uuid4().hex
        sub_unhealthy = uuid.uuid4().hex
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[sub_healthy, sub_unhealthy])

        with patch.object(monitor, '_probe_subsystem') as mock_probe:
            def side_effect_func(name):
                status = SubsystemHealthStatus.UNHEALTHY if name == sub_unhealthy else SubsystemHealthStatus.DEGRADED
                return {
                    "subsystem": name,
                    "status": status,
                    "token": None,
                    "error": uuid.uuid4().hex
                }
            mock_probe.side_effect = side_effect_func

            audit_result = monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)

    def test_verify_stream_pipeline_success(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()
        rand_url = f"http://{uuid.uuid4().hex}.local/{uuid.uuid4().hex}"
        rand_content = uuid.uuid4().bytes * random.randint(1, 10)

        with patch("requests.get") as mock_get:
            mock_response = mock_get.return_value
            mock_response.content = rand_content

            result = monitor.verify_stream_pipeline(rand_url)
            mock_get.assert_called_once_with(rand_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(rand_content))

    def test_verify_stream_pipeline_failure(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()
        rand_url = f"http://{uuid.uuid4().hex}.local/{uuid.uuid4().hex}"

        with patch("requests.get") as mock_get:
            mock_get.side_effect = requests.RequestException(uuid.uuid4().hex)

            result = monitor.verify_stream_pipeline(rand_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_dynamic_getattr_hook(self):
        rand_attr = uuid.uuid4().hex
        rand_payload = uuid.uuid4().hex

        dynamic_func = __getattr__(rand_attr)
        res = dynamic_func(rand_payload)

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["payload"], rand_payload)