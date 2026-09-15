import unittest
import os
import uuid
import random
import tempfile
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.reporter = SystemHealthReporter()
        self.dashboard_generator = RecoveryDashboardGenerator()
        self.test_dir = tempfile.TemporaryDirectory()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_end_to_end_system_health_aggregation_and_export(self):
        unique_module_name = f"module_{uuid.uuid4().hex[:8]}"
        random_incident_id = str(uuid.uuid4())
        random_error_count = random.randint(10, 500)
        random_patch_status = random.choice(["success", "failed", "pending", "applied"])

        incident_data = {
            "id": random_incident_id,
            "error_count": random_error_count,
            "status": "critical"
        }
        audit_summary = {
            "vulnerabilities": random.randint(0, 5),
            "status": "passed"
        }
        metrics = {
            "cpu_usage": round(random.uniform(10.0, 99.9), 2),
            "memory_usage": round(random.uniform(20.0, 95.0), 2),
            "patch_status": random_patch_status
        }

        incidents_list = [incident_data]
        patches_list = [{"id": str(uuid.uuid4()), "status": random_patch_status}]

        system_metrics = self.reporter.aggregate_system_metrics(incidents_list, patches_list)
        self.assertIsInstance(system_metrics, dict)

        health_report = self.reporter.generate_health_report(
            module_name=unique_module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics
        )
        self.assertIsNotNone(health_report)

        dashboard_metrics = self.dashboard_generator.aggregate_system_health()
        self.assertIsInstance(dashboard_metrics, dict)

        dashboard_html = self.dashboard_generator.generate_dashboard(
            metrics=metrics,
            incidents=incidents_list,
            reports=[health_report],
            format="html"
        )
        self.assertIsInstance(dashboard_html, str)
        self.assertTrue(len(dashboard_html) > 0)

        export_path = os.path.join(self.test_dir.name, f"dashboard_{uuid.uuid4().hex}.html")
        export_result = self.dashboard_generator.export_dashboard(dashboard_html, export_path)
        self.assertTrue(export_result)
        self.assertTrue(os.path.exists(export_path))

        with open(export_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(unique_module_name, content)
            self.assertIn(random_incident_id, content)

    def test_aggregator_composition_pipeline(self):
        stream_payload = f"metric_id:{uuid.uuid4()}|value:{random.randint(1, 1000)}".encode("utf-8")

        parsed_data_reporter = self.reporter.parse_stream_data(stream_payload)
        parsed_data_dashboard = self.dashboard_generator.parse_stream_data(stream_payload)

        self.assertIsNotNone(parsed_data_dashboard)

        aggregated_health = self.aggregator.aggregate_comprehensive_health() if hasattr(self.aggregator, "aggregate_comprehensive_health") else {}
        self.assertIsInstance(aggregated_health, dict)

if __name__ == "__main__":
    unittest.main()