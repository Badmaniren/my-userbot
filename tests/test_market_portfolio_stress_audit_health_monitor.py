import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.market_portfolio_stress_audit_health_monitor import (
    MarketPortfolioStressAuditHealthMonitor,
    SubsystemHealthStatus,
    HealthMonitorExecutionError,
    StorageUnreachableError
)

class TestMarketPortfolioStressAuditHealthMonitor(unittest.TestCase):

    def setUp(self):
        self.random_prefix = uuid.uuid4().hex[:8]
        self.monitored_subsystems = [
            f"db_storage_{self.random_prefix}",
            f"extractor_tool_{random.randint(100000000, 999999999)}",
            f"market_portfolio_stress_audit_summary_vault_{self.random_prefix}",
            f"market_portfolio_stress_scenario_pipeline_{self.random_prefix}"
        ]
        self.monitor = MarketPortfolioStressAuditHealthMonitor(subsystems=self.monitored_subsystems)

    def test_initialization_state(self):
        self.assertEqual(len(self.monitor.subsystems), len(self.monitored_subsystems))
        for sub in self.monitored_subsystems:
            self.assertIn(sub, self.monitor.subsystems)

    def test_health_check_all_success(self):
        expected_token = uuid.uuid4().hex
        
        def mock_health_probe(subsystem_name):
            return {
                "subsystem": subsystem_name,
                "status": SubsystemHealthStatus.HEALTHY,
                "token": expected_token,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_health_probe):
            report = self.monitor.run_full_audit()

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("global_status"), SubsystemHealthStatus.HEALTHY)
        self.assertIn("subsystems_details", report)
        
        for sub in self.monitored_subsystems:
            self.assertIn(sub, report["subsystems_details"])
            self.assertEqual(report["subsystems_details"][sub]["token"], expected_token)
            self.assertEqual(report["subsystems_details"][sub]["status"], SubsystemHealthStatus.HEALTHY)

    def test_health_check_storage_failure_raises_exception(self):
        failed_storage = self.monitored_subsystems[0]
        random_error_message = f"Storage timeout {uuid.uuid4().hex}"

        def mock_failing_probe(subsystem_name):
            if subsystem_name == failed_storage:
                raise StorageUnreachableError(random_error_message)
            return {
                "subsystem": subsystem_name,
                "status": SubsystemHealthStatus.HEALTHY,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_failing_probe):
            with self.assertRaises(StorageUnreachableError) as ctx:
                self.monitor.run_full_audit()
            
            self.assertIn(random_error_message, str(ctx.exception))

    def test_pipeline_degradation_handling(self):
        degraded_pipeline = random.choice(self.monitored_subsystems)
        random_warning = f"Pipeline latency high: {uuid.uuid4().hex}"

        def mock_degraded_probe(subsystem_name):
            if subsystem_name == degraded_pipeline:
                return {
                    "subsystem": subsystem_name,
                    "status": SubsystemHealthStatus.DEGRADED,
                    "error": random_warning
                }
            return {
                "subsystem": subsystem_name,
                "status": SubsystemHealthStatus.HEALTHY,
                "error": None
            }

        with patch.object(self.monitor, '_probe_subsystem', side_effect=mock_degraded_probe):
            report = self.monitor.run_full_audit()

        self.assertEqual(report.get("global_status"), SubsystemHealthStatus.DEGRADED)
        self.assertEqual(report["subsystems_details"][degraded_pipeline]["status"], SubsystemHealthStatus.DEGRADED)
        self.assertEqual(report["subsystems_details"][degraded_pipeline]["error"], random_warning)

    def test_stream_ingestor_and_sink_verification(self):
        random_payload = b"".join(random.choices(string.ascii_bytes + string.digits_bytes, k=128))
        mock_stream = io.BytesIO(random_payload)

        subsystem_target = f"market_portfolio_realtime_stream_ingestor_{uuid.uuid4().hex[:6]}"
        
        with patch('skills.market_portfolio_stress_audit_health_monitor.requests.get') as mock_requests_get:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.raw = mock_stream
            mock_response.content = random_payload
            mock_requests_get.return_value = mock_response

            result = self.monitor.verify_stream_pipeline(subsystem_target)

        self.assertTrue(result.get("is_active"))
        self.assertEqual(result.get("bytes_read"), len(random_payload))

    def test_unexpected_execution_error_propagates(self):
        random_exception_msg = f"Critical kernel panic {uuid.uuid4().hex}"

        with patch.object(self.monitor, '_probe_subsystem', side_effect=RuntimeError(random_exception_msg)):
            with self.assertRaises(HealthMonitorExecutionError) as ctx:
                self.monitor.run_full_audit()
            
            self.assertIn(random_exception_msg, str(ctx.exception))