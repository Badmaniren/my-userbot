import unittest
import uuid
import random
import os
from skills.incident_trend_reporter import incident_trend_reporter
from skills.incident_aggregator import incident_aggregator
from skills.incident_trend_analyzer import incident_trend_analyzer

class TestIncidentTrendReporterIntegration(unittest.TestCase):
    def test_trend_reporter_real_integration(self):
        random_suffix = uuid.uuid4().hex[:8]
        test_incident_id = f"INC-{random_suffix}"
        test_severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        raw_data = {
            "id": test_incident_id,
            "severity": test_severity_level,
            "metric": random.randint(10, 100500)
        }

        aggregated = incident_aggregator(raw_data)
        self.assertIsNotNone(aggregated)

        analyzed_trends = incident_trend_analyzer(aggregated)
        self.assertIsNotNone(analyzed_trends)

        report_output = incident_trend_reporter(analyzed_trends)
        self.assertIsInstance(report_output, dict)
        self.assertIn("report_id", report_output)

        expected_file_path = f"reports/trend_report_{test_incident_id}.json"
        if "file_path" in report_output:
            self.assertTrue(os.path.exists(report_output["file_path"]))

if __name__ == "__main__":
    unittest.main()