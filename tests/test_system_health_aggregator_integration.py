import unittest
import uuid
import random
import os
import tempfile
from skills.system_health_aggregator import SystemHealthAggregator
from skills.system_health_reporter import SystemHealthReporter
from skills.recovery_dashboard_generator import RecoveryDashboardGenerator

class TestSystemHealthAggregatorIntegration(unittest.TestCase):
    def setUp(self):
        self.aggregator = SystemHealthAggregator()
        self.reporter = SystemHealthReporter()
        self.dashboard_gen = RecoveryDashboardGenerator()
        self.test_dir = tempfile.mkdtemp()

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            os.rmdir(root)

    def test_end_to_end_health_aggregation_and_dashboard(self):
        random_module_name = f"module_{uuid.uuid4().hex[:8]}"
        random_metric_value = random.randint(100, 999)
        random_incident_id = str(uuid.uuid4())

        incident_data = {
            "id": random_incident_id,
            "status": "resolved",
            "severity": "high"
        }
        audit_summary = {
            "status": "passed",
            "score": random_metric_value
        }
        metrics = {
            "cpu_usage": random.uniform(10.0, 90.0),
            "memory_usage": random.uniform(20.0, 80.0),
            "custom_metric": random_metric_value
        }
        incidents_list = [incident_data]
        patches_list = [{"id": uuid.uuid4().hex, "status": "applied"}]

        report = self.reporter.generate_health_report(
            module_name=random_module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics
        )

        self.assertIsNotNone(report)

        dashboard_payload = self.dashboard_gen.generate_dashboard(
            metrics=metrics,
            incidents=incidents_list,
            reports=[report],
            format="json"
        )

        self.assertIsNotNone(dashboard_payload)

        aggregated_health = self.dashboard_gen.aggregate_system_health()
        self.assertIsInstance(aggregated_health, dict)

        comprehensive_analysis = self.aggregator.collect_and_aggregate(
            module_name=random_module_name,
            incident_data=incident_data,
            audit_summary=audit_summary,
            metrics=metrics,
            incidents_list=incidents_list,
            patches_list=patches_list
        )

        self.assertIsInstance(comprehensive_analysis, dict)
        
        analysis_str = str(comprehensive_analysis)
        self.assertIn(random_module_name, analysis_str)
        self.assertIn(str(random_metric_value), analysis_str)
        self.assertIn(random_incident_id, analysis_str)

        file_path = os.path.join(self.test_dir, f"dashboard_{uuid.uuid4().hex}.json")
        export_result = self.dashboard_gen.export_dashboard(comprehensive_analysis, file_path)
        
        if export_result is not None:
            self.assertTrue(export_result)
        
        self.assertTrue(os.path.exists(file_path))
        with open(file_path, "r", encoding="utf-8") as f:
            file_content = f.read()
            self.assertIn(random_module_name, file_content)

if __name__ == "__main__":
    unittest.main()