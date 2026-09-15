import unittest
import os
import shutil
import uuid
import random
import json
from skills.incident_severity_evaluator import IncidentSeverityEvaluator, evaluate_incident_severity
from skills.incident_aggregator import aggregate_incidents
from skills.vulnerability_scanner import scan_vulnerabilities
from skills.system_health_telemetry_collector import collect_telemetry

class TestIncidentSeverityEvaluatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = f"./test_output_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_end_to_end_severity_evaluation_pipeline(self):
        unique_incident_id = str(uuid.uuid4())
        random_cvss = round(random.uniform(1.0, 10.0), 1)
        random_error_rate = round(random.uniform(0.0, 1.0), 2)
        random_unauthorized = random.randint(0, 1000)

        raw_telemetry = {
            "cvss_score": random_cvss,
            "active_exploits": random.choice([True, False]),
            "error_rate": random_error_rate,
            "unauthorized_access_attempts": random_unauthorized
        }

        collected_telemetry = collect_telemetry(raw_telemetry)
        scanned_vulns = scan_vulnerabilities([{"id": unique_incident_id, "severity": "CRITICAL", "exploit_available": True}])
        aggregated = aggregate_incidents([{"incident_id": unique_incident_id, "telemetry": collected_telemetry, "vulnerabilities": scanned_vulns}])

        evaluator = IncidentSeverityEvaluator()
        risk_factor = evaluator.calculate_risk_factor(collected_telemetry)
        self.assertIsInstance(risk_factor, float)

        incident_payload = {
            "incident_id": unique_incident_id,
            "telemetry": collected_telemetry,
            "vulnerabilities": scanned_vulns
        }

        report = evaluate_incident_severity(incident_payload, output_path=self.test_dir)

        self.assertEqual(report["incident_id"], unique_incident_id)
        self.assertIn("severity_level", report)
        self.assertIn("score", report)

        expected_file_name = f"severity_{unique_incident_id}.json"
        expected_file_path = os.path.join(self.test_dir, expected_file_name)
        self.assertTrue(os.path.exists(expected_file_path), "Файл отчета не был создан на диске")

        with open(expected_file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["incident_id"], unique_incident_id)
        self.assertEqual(saved_data["severity_level"], report["severity_level"])
        self.assertEqual(saved_data["score"], report["score"])

if __name__ == "__main__":
    unittest.main()