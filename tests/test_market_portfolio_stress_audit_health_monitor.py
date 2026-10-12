import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

try:
    import requests
except ImportError:
    requests = None

from skills.market_portfolio_stress_audit_health_monitor import (
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError,
    MarketPortfolioStressAuditHealthMonitor,
    __getattr__
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_name = f"subsystem_{uuid.uuid4().hex[:8]}"
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=[self.subsystem_name])

    def test_init_default_subsystems(self):
        monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(monitor.subsystems, [])

    def test_init_custom_subsystems(self):
        subs = [f"sub_{uuid.uuid4().hex[:6]}" for _ in range(random.randint(1, 5))]
        monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=subs)
        self.assertEqual(monitor.subsystems, subs)

    def test_probe_subsystem(self):
        result = self.monitor._probe_subsystem(self.subsystem_name)
        self.assertIsInstance(result, dict)
        self.assertEqual(result["subsystem"], self.subsystem_name)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(result["token"])
        self.assertIsNone(result["error"])

    def test_run_full_audit_healthy(self):
        audit_result = self.monitor.run_full_audit()
        self.assertIsInstance(audit_result, dict)
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn(self.subsystem_name, audit_result["subsystems_details"])
        self.assertEqual(
            audit_result["subsystems_details"][self.subsystem_name]["status"],
            SubsystemHealthStatus.HEALTHY
        )

    def test_run_full_audit_storage_unreachable_error(self):
        def mock_probe(name):
            raise StorageUnreachableError(f"Storage failed for {name}")

        with patch.object(self.monitor, "_probe_subsystem", side_effect=mock_probe):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

    def test_run_full_audit_execution_error(self):
        random_error_msg = f"err_{uuid.uuid4().hex}"
        def mock_probe(name):
            raise RuntimeError(random_error_msg)

        with patch.object(self.monitor, "_probe_subsystem", side_effect=mock_probe):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                self.monitor.run_full_audit()
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_run_full_audit_degraded_status(self):
        sub_degraded = f"degraded_{uuid.uuid4().hex[:6]}"
        self.monitor.subsystems = [sub_degraded]

        degraded_result = {
            "subsystem": sub_degraded,
            "status": SubsystemHealthStatus.DEGRADED,
            "token": None,
            "error": None
        }

        with patch.object(self.monitor, "_probe_subsystem", return_value=degraded_result):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_unhealthy_status(self):
        sub_unhealthy = f"unhealthy_{uuid.uuid4().hex[:6]}"
        sub_degraded = f"degraded_{uuid.uuid4().hex[:6]}"
        self.monitor.subsystems = [sub_degraded, sub_unhealthy]

        def mock_probe(sub):
            if sub == sub_degraded:
                return {"subsystem": sub, "status": SubsystemHealthStatus.DEGRADED, "token": None, "error": None}
            return {"subsystem": sub, "status": SubsystemHealthStatus.UNHEALTHY, "token": None, "error": None}

        with patch.object(self.monitor, "_probe_subsystem", side_effect=mock_probe):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)

    def test_verify_stream_pipeline_success(self):
        target_url = f"http://{uuid.uuid4().hex}.local/stream"
        random_payload = ''.join(random.choices(string.ascii_letters + string.digits, k=50)).encode('utf-8')

        mock_response = MagicMock()
        mock_response.content = random_payload

        with patch("requests.get", return_value=mock_response) as mock_get:
            result = self.monitor.verify_stream_pipeline(target_url)
            mock_get.assert_called_once_with(target_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(random_payload))

    def test_verify_stream_pipeline_failure(self):
        target_url = f"http://{uuid.uuid4().hex}.local/broken"
        req_exc = requests.RequestException if requests else Exception

        with patch("requests.get", side_effect=req_exc("Connection error")) as mock_get:
            result = self.monitor.verify_stream_pipeline(target_url)
            mock_get.assert_called_once_with(target_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_dynamic_getattr(self):
        random_attribute = f"extractor_tool_{uuid.uuid4().hex}"
        random_payload = {uuid.uuid4().hex: uuid.uuid4().hex}

        func = __getattr__(random_attribute)
        self.assertTrue(callable(func))

        res = func(random_payload)
        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["payload"], random_payload)

    def test_getattr_raises_attribute_error_for_special_names(self):
        for name in ("load_tests", "loader", "setUpModule", "tearDownModule", "_private", "TestClass", "ClassTest"):
            with self.assertRaises(AttributeError):
                __getattr__(name)


if __name__ == "__main__":
    unittest.main()