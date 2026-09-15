import unittest
import uuid
import random
import os
import tempfile

from skills.incident_severity_evaluator import evaluate_incident_severity
from skills.incident_aggregator import aggregate_incidents
from skills.vulnerability_scanner import scan_vulnerabilities
from skills.system_health_telemetry_collector import collect_telemetry

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.incident_id = str(uuid.uuid4())
        self.service_name = f"service-{random.randint(1000, 9999)}"

    def tearDown(self):
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_evaluate_incident_severity_end_to_end(self):
        raw_telemetry = collect_telemetry(
            service_name=self.service_name,
            error_rate=random.uniform(5.0, 50.0),
            response_time_ms=random.randint(500, 5000)
        )

        scan_results = scan_vulnerabilities(
            target=self.service_name,
            scan_depth=random.choice(["deep", "quick"])
        )

        aggregated_data = aggregate_incidents(
            incident_id=self.incident_id,
            telemetry=raw_telemetry,
            vulnerabilities=scan_results
        )

        severity_report = evaluate_incident_severity(
            incident_data=aggregated_data,
            output_path=self.test_dir
        )

        self.assertIn("severity_level", severity_report)
        self.assertEqual(severity_report.get("incident_id"), self.incident_id)

        expected_file_name = f"severity_{self.incident_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        
        self.assertTrue(
            os.path.exists(expected_file_path),
            f"Integration failure: Severity report file {expected_file_path} was not created."
        )

        with open(expected_file_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.incident_id, content)

if __name__ == "__main__":
    unittest.main()