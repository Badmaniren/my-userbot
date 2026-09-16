import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
from types import ModuleType

class MockModule(ModuleType):
    def __getattr__(self, name):
        return MagicMock()

for mod_name in [
    "auto_patch_pipeline", "dependency_audit_reporter", "error_recovery_hub",
    "extractor_tool_1789544538", "incident_aggregator", "incident_auto_escalation_engine",
    "incident_auto_recovery_dispatcher", "incident_impact_analyzer", "incident_knowledge_base_searcher",
    "incident_notification_bridge", "incident_notification_broadcaster", "incident_post_mortem_service",
    "incident_severity_evaluator", "incident_trend_analyzer", "incident_trend_forecaster",
    "notification_channel_dispatcher", "notification_template_engine", "notification_webhook_broadcaster",
    "package_requirement_reader", "patch_auto_executor", "patch_metric_collector",
    "patch_scheduler", "patch_validator", "preventive_patch_applier", "pypi_client",
    "recovery_dashboard_generator", "recovery_report_exporter", "system_health_aggregator",
    "system_health_audit_pipeline", "system_health_monitoring_gateway", "system_health_reporter",
    "system_health_telemetry_collector", "vulnerability_scanner"
]:
    sys.modules[mod_name] = MockModule(mod_name)

from skills import incident_business_loss_estimator

class TestIncidentBusinessLossEstimator(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: uuid.uuid4().hex
        self.rand_float = lambda: round(random.uniform(100.0, 100000.0), 2)
        self.rand_int = lambda: random.randint(1, 1440)

    def test_estimate_financial_loss_basic(self):
        downtime_minutes = self.rand_int()
        cost_per_minute = self.rand_float()
        expected_loss = downtime_minutes * cost_per_minute

        impact_data = {
            "downtime_minutes": downtime_minutes,
            "cost_per_minute": cost_per_minute,
            "incident_id": self.rand_str()
        }

        estimator = incident_business_loss_estimator.IncidentBusinessLossEstimator()
        result = estimator.calculate_financial_loss(impact_data)

        self.assertIn("total_loss", result)
        self.assertEqual(result["total_loss"], expected_loss)
        self.assertEqual(result["incident_id"], impact_data["incident_id"])

    def test_estimate_operational_impact_with_mock(self):
        rand_component = self.rand_str()
        rand_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        rand_loss_factor = self.rand_float()

        mock_impact_analyzer = MagicMock()
        mock_impact_analyzer.get_metrics.return_value = {
            "component": rand_component,
            "severity": rand_severity,
            "loss_factor": rand_loss_factor
        }

        with patch("skills.incident_business_loss_estimator.incident_impact_analyzer", mock_impact_analyzer):
            estimator = incident_business_loss_estimator.IncidentBusinessLossEstimator()
            assessment = estimator.evaluate_operational_impact(self.rand_str())

            self.assertEqual(assessment["component"], rand_component)
            self.assertEqual(assessment["severity"], rand_severity)
            self.assertGreaterEqual(assessment["operational_score"], 0.0)

    def test_loss_report_export_stream(self):
        rand_key = self.rand_str()
        rand_val = self.rand_float()
        report_data = {rand_key: rand_val}

        estimator = incident_business_loss_estimator.IncidentBusinessLossEstimator()
        stream = estimator.export_loss_report_stream(report_data)

        self.assertIsInstance(stream, io.BytesIO)
        content = stream.read().decode("utf-8")
        self.assertIn(rand_key, content)
        self.assertIn(str(rand_val), content)

    def test_calculate_aggregate_losses_empty_list(self):
        estimator = incident_business_loss_estimator.IncidentBusinessLossEstimator()
        result = estimator.calculate_aggregate_losses([])
        self.assertEqual(result.get("total_aggregate_loss"), 0.0)
        self.assertEqual(result.get("incident_count"), 0)

    def test_calculate_aggregate_losses_multiple(self):
        incidents = []
        total_expected = 0.0
        for _ in range(random.randint(3, 8)):
            loss = self.rand_float()
            total_expected += loss
            incidents.append({
                "incident_id": self.rand_str(),
                "total_loss": loss
            })

        estimator = incident_business_loss_estimator.IncidentBusinessLossEstimator()
        result = estimator.calculate_aggregate_losses(incidents)

        self.assertAlmostEqual(result["total_aggregate_loss"], total_expected, places=2)
        self.assertEqual(result["incident_count"], len(incidents))

    def test_loss_estimator_with_corrupted_stream(self):
        garbage_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=128)).encode("utf-8")
        stream = io.BytesIO(garbage_bytes)

        estimator = incident_business_loss_estimator.IncidentBusinessLossEstimator()
        with self.assertRaises(Exception):
            estimator.parse_loss_from_stream(stream)

if __name__ == "__main__":
    unittest.main()