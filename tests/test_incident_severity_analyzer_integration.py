import unittest
import uuid
import random
import os
import tempfile
from skills.incident_severity_analyzer import IncidentSeverityAnalyzer
from skills.incident_aggregator import IncidentAggregator
from skills.system_health_telemetry_collector import SystemHealthTelemetryCollector

class TestIncidentSeverityAnalyzerIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.telemetry_collector = SystemHealthTelemetryCollector()
        self.incident_aggregator = IncidentAggregator()
        self.analyzer = IncidentSeverityAnalyzer()

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_intelligent_prioritization_epic_flow(self):
        random_seed_id = str(uuid.uuid4())
        metric_value = random.uniform(10.0, 100.0)

        telemetry_data = self.telemetry_collector.collect(
            source_id=random_seed_id,
            load_factor=metric_value
        )

        aggregated_incident = self.incident_aggregator.aggregate(
            telemetry=telemetry_data,
            incident_tag=f"tag_{random_seed_id[:8]}"
        )

        analysis_result = self.analyzer.analyze(
            incident=aggregated_incident,
            output_dir=self.test_dir
        )

        self.assertIn("severity_score", analysis_result)
        self.assertEqual(analysis_result["target_incident_id"], random_seed_id)

        report_filename = f"severity_report_{random_seed_id}.json"
        expected_file_path = os.path.join(self.test_dir, report_filename)

        self.assertTrue(
            os.path.exists(expected_file_path),
            f"Integration failed: Analyzer did not produce expected report at {expected_file_path}"
        )

        with open(expected_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(random_seed_id, content)

if __name__ == "__main__":
    unittest.main()