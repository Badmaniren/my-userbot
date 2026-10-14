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
    MarketPortfolioStressAuditHealthMonitor,
    __getattr__
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_count = random.randint(1, 5)
        self.subsystems = [f"subsystem_{uuid.uuid4().hex[:8]}" for _ in range(self.subsystem_count)]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.subsystems)

    def test_init_and_default_subsystems(self):
        empty_monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(empty_monitor.subsystems, [])
        self.assertEqual(self.monitor.subsystems, self.subsystems)

    def test_probe_subsystem_returns_structure(self):
        target_sub = random.choice(self.subsystems)
        result = self.monitor._probe_subsystem(target_sub)
        self.assertIn("subsystem", result)
        self.assertEqual(result["subsystem"], target_sub)
        self.assertIn("status", result)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn("token", result)
        self.assertIn("error", result)

    def test_run_full_audit_all_healthy(self):
        audit_result = self.monitor.run_full_audit()
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertEqual(len(audit_result["subsystems_details"]), len(self.subsystems))
        for sub in self.subsystems:
            self.assertIn(sub, audit_result["subsystems_details"])
            self.assertEqual(audit_result["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_storage_unreachable_exception(self):
        target_sub = random.choice(self.subsystems)
        err_msg = uuid.uuid4().hex

        def mock_probe(sub):
            if sub == target_sub:
                raise StorageUnreachableError(err_msg)
            return {
                "subsystem": sub,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

    def test_run_full_audit_generic_execution_error(self):
        target_sub = random.choice(self.subsystems)
        err_msg = uuid.uuid4().hex

        def mock_probe(sub):
            if sub == target_sub:
                raise RuntimeError(err_msg)
            return {
                "subsystem": sub,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                self.monitor.run_full_audit()
            self.assertIn(err_msg, str(ctx.exception))

    def test_run_full_audit_global_status_degraded(self):
        degraded_sub = random.choice(self.subsystems)

        def mock_probe(sub):
            status = SubsystemHealthStatus.DEGRADED if sub == degraded_sub else SubsystemHealthStatus.HEALTHY
            return {
                "subsystem": sub,
                "status": status,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_global_status_unhealthy(self):
        unhealthy_sub = random.choice(self.subsystems)

        def mock_probe(sub):
            status = SubsystemHealthStatus.UNHEALTHY if sub == unhealthy_sub else SubsystemHealthStatus.HEALTHY
            return {
                "subsystem": sub,
                "status": status,
                "token": None,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_probe):
            audit_result = self.monitor.run_full_audit()
            self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.UNHEALTHY)

    def test_verify_stream_pipeline_success(self):
        random_url = f"http://{uuid.uuid4().hex}.local/{uuid.uuid4().hex}"
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 100))).encode('utf-8')

        mock_response = MagicMock()
        mock_response.content = random_bytes

        with patch('requests.get', return_value=mock_response) as mock_get:
            result = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertTrue(result["is_active"])
            self.assertEqual(result["bytes_read"], len(random_bytes))

    def test_verify_stream_pipeline_failure(self):
        random_url = f"http://{uuid.uuid4().hex}.local/{uuid.uuid4().hex}"
        err_msg = uuid.uuid4().hex

        with patch('requests.get', side_effect=requests.RequestException(err_msg)) as mock_get:
            result = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertFalse(result["is_active"])
            self.assertEqual(result["bytes_read"], 0)

    def test_module_getattr_fallback(self):
        attr_name = f"dynamic_fallback_{uuid.uuid4().hex}"
        random_payload = uuid.uuid4().hex

        dynamic_func = __getattr__(attr_name)
        res = dynamic_func(random_payload)

        self.assertEqual(res["status"], "ok")
        self.assertEqual(res["payload"], random_payload)