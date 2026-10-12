import unittest
from unittest.mock import patch
import random
import uuid
import string
import requests
import io

from skills.market_portfolio_stress_audit_health_monitor import (
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError,
    MarketPortfolioStressAuditHealthMonitor
)


class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.subsystem_name_1 = f"sub_{uuid.uuid4().hex[:8]}"
        self.subsystem_name_2 = f"sub_{uuid.uuid4().hex[:8]}"
        self.subsystems = [self.subsystem_name_1, self.subsystem_name_2]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(self.subsystems)

    def test_init_default_subsystems(self):
        random_monitor = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(random_monitor.subsystems, [])

    def test_init_custom_subsystems(self):
        custom_sub = f"sub_{uuid.uuid4().hex}"
        random_monitor = MarketPortfolioStressAuditHealthMonitor([custom_sub])
        self.assertEqual(random_monitor.subsystems, [custom_sub])

    def test_init_invalid_subsystems(self):
        with self.assertRaises(TypeError):
            MarketPortfolioStressAuditHealthMonitor("not-a-list")

    def test_probe_subsystem_structure(self):
        rand_sub = f"sub_{uuid.uuid4().hex}"
        result = self.monitor._probe_subsystem(rand_sub)
        self.assertEqual(result["subsystem"], rand_sub)
        self.assertEqual(result["status"], SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(result["token"])
        self.assertIsNone(result["error"])

    def test_probe_subsystem_invalid(self):
        with self.assertRaises(ValueError):
            self.monitor._probe_subsystem("")

    def test_run_full_audit_success(self):
        audit_result = self.monitor.run_full_audit()
        self.assertEqual(audit_result["global_status"], SubsystemHealthStatus.HEALTHY)
        self.assertIn(self.subsystem_name_1, audit_result["subsystems_details"])
        self.assertIn(self.subsystem_name_2, audit_result["subsystems_details"])

    def test_run_full_audit_storage_unreachable(self):
        rand_err_msg = "".join(random.choices(string.ascii_letters, k=10))
        with patch.object(
            self.monitor,
            "_probe_subsystem",
            side_effect=StorageUnreachableError(rand_err_msg)
        ):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

    def test_run_full_audit_execution_error(self):
        rand_err_msg = "".join(random.choices(string.ascii_letters, k=12))
        with patch.object(
            self.monitor,
            "_probe_subsystem",
            side_effect=RuntimeError(rand_err_msg)
        ):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                self.monitor.run_full_audit()
            self.assertIn(rand_err_msg, str(ctx.exception))

    def test_verify_stream_pipeline_success(self):
        rand_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=6))}.local/{uuid.uuid4().hex}"
        rand_payload = "".join(random.choices(string.printable, k=random.randint(10, 50))).encode("utf-8")

        mock_response = requests.Response()
        mock_response.status_code = 200
        mock_response.raw = io.BytesIO(rand_payload)

        with patch("requests.get", return_value=mock_response) as mock_get:
            with patch.object(type(mock_response), "content", new_callable=lambda: rand_payload):
                res = self.monitor.verify_stream_pipeline(rand_url)
                self.assertTrue(res["is_active"])
                self.assertEqual(res["bytes_read"], len(rand_payload))
                mock_get.assert_called_once_with(rand_url)

    def test_verify_stream_pipeline_failure(self):
        rand_url = f"http://{''.join(random.choices(string.ascii_lowercase, k=6))}.local/{uuid.uuid4().hex}"
        rand_err = "".join(random.choices(string.ascii_letters, k=8))

        with patch("requests.get", side_effect=Exception(rand_err)) as mock_get:
            with self.assertRaises(Exception):
                self.monitor.verify_stream_pipeline(rand_url)
            mock_get.assert_called_once_with(rand_url)


if __name__ == "__main__":
    unittest.main()
