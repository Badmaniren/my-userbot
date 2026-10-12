import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
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

    def setUp(self) -> None:
        self.random_subsystem_1 = f"sub_{uuid.uuid4().hex[:8]}"
        self.random_subsystem_2 = f"sub_{uuid.uuid4().hex[:8]}"
        self.monitor = MarketPortfolioStressAuditHealthMonitor(
            subsystems=[self.random_subsystem_1, self.random_subsystem_2]
        )

    def test_init_defaults(self) -> None:
        monitor_default = MarketPortfolioStressAuditHealthMonitor()
        self.assertEqual(monitor_default.subsystems, [])
        self.assertIsNotNone(monitor_default.db)

    def test_probe_subsystem_returns_expected_structure(self) -> None:
        probe_name = f"probe_{uuid.uuid4().hex[:6]}"
        result = self.monitor._probe_subsystem(probe_name)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("subsystem"), probe_name)
        self.assertEqual(result.get("status"), SubsystemHealthStatus.HEALTHY)
        self.assertIsNone(result.get("token"))
        self.assertIsNone(result.get("error"))

    def test_run_full_audit_healthy(self) -> None:
        audit_result = self.monitor.run_full_audit()

        self.assertIsInstance(audit_result, dict)
        self.assertEqual(audit_result.get("global_status"), SubsystemHealthStatus.HEALTHY)

        details = audit_result.get("subsystems_details", {})
        self.assertIn(self.random_subsystem_1, details)
        self.assertIn(self.random_subsystem_2, details)
        self.assertEqual(details[self.random_subsystem_1]["status"], SubsystemHealthStatus.HEALTHY)

    def test_run_full_audit_storage_unreachable_raises(self) -> None:
        err_msg = f"storage_fail_{uuid.uuid4().hex[:6]}"
        with patch.object(
            self.monitor,
            "_probe_subsystem",
            side_effect=StorageUnreachableError(err_msg)
        ):
            with self.assertRaises(StorageUnreachableError):
                self.monitor.run_full_audit()

    def test_run_full_audit_general_exception_raises_execution_error(self) -> None:
        err_msg = f"generic_fail_{uuid.uuid4().hex[:6]}"
        with patch.object(
            self.monitor,
            "_probe_subsystem",
            side_effect=RuntimeError(err_msg)
        ):
            with self.assertRaises(HealthMonitorExecutionError):
                self.monitor.run_full_audit()

    def test_run_full_audit_global_status_degraded(self) -> None:
        degraded_sub = f"deg_{uuid.uuid4().hex[:6]}"
        monitor_deg = MarketPortfolioStressAuditHealthMonitor(subsystems=[degraded_sub])

        with patch.object(
            monitor_deg,
            "_probe_subsystem",
            return_value={
                "subsystem": degraded_sub,
                "status": SubsystemHealthStatus.DEGRADED,
                "token": None,
                "error": None
            }
        ):
            audit_result = monitor_deg.run_full_audit()
            self.assertEqual(audit_result.get("global_status"), SubsystemHealthStatus.DEGRADED)

    def test_run_full_audit_global_status_unhealthy(self) -> None:
        unhealthy_sub = f"unh_{uuid.uuid4().hex[:6]}"
        monitor_unh = MarketPortfolioStressAuditHealthMonitor(subsystems=[unhealthy_sub])

        with patch.object(
            monitor_unh,
            "_probe_subsystem",
            return_value={
                "subsystem": unhealthy_sub,
                "status": SubsystemHealthStatus.UNHEALTHY,
                "token": None,
                "error": "critical"
            }
        ):
            audit_result = monitor_unh.run_full_audit()
            self.assertEqual(audit_result.get("global_status"), SubsystemHealthStatus.UNHEALTHY)

    def test_verify_stream_pipeline_success(self) -> None:
        random_url = f"https://{uuid.uuid4().hex[:10]}.test/stream"
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")

        mock_response = MagicMock()
        mock_response.content = random_bytes

        with patch("requests.get", return_value=mock_response) as mock_get:
            res = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertTrue(res.get("is_active"))
            self.assertEqual(res.get("bytes_read"), len(random_bytes))

    def test_verify_stream_pipeline_failure(self) -> None:
        random_url = f"https://{uuid.uuid4().hex[:10]}.test/broken"

        with patch("requests.get", side_effect=requests.RequestException("Network down")) as mock_get:
            res = self.monitor.verify_stream_pipeline(random_url)
            mock_get.assert_called_once_with(random_url)
            self.assertFalse(res.get("is_active"))
            self.assertEqual(res.get("bytes_read"), 0)