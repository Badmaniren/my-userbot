import unittest
import os
import json
import uuid
import random
from skills.incident_forensic_analyzer import incident_forensic_analyzer, start_new

class TestIncidentForensicAnalyzerIntegration(unittest.TestCase):

    def test_forensic_analyzer_report_generation(self):
        unique_id = f"inc-{uuid.uuid4()}"
        random_metric = random.randint(100, 9999)

        payload = {
            "telemetry_ref": {
                "metric_val": random_metric
            },
            "description": f"Test anomaly {uuid.uuid4()}"
        }

        output_file = os.path.join("test_reports", f"{unique_id}_report.json")

        try:
            result = incident_forensic_analyzer(unique_id, payload, output_file)

            self.assertIsInstance(result, dict)
            self.assertEqual(result.get("target_incident_id"), unique_id)
            self.assertEqual(result.get("metric_val"), random_metric)
            self.assertEqual(result.get("payload"), payload)

            self.assertTrue(os.path.exists(output_file))

            with open(output_file, "r", encoding="utf-8") as f:
                file_data = json.load(f)

            self.assertEqual(file_data.get("target_incident_id"), unique_id)
            self.assertEqual(file_data.get("metric_val"), random_metric)

        finally:
            if os.path.exists(output_file):
                os.remove(output_file)
            if os.path.exists("test_reports") and not os.listdir("test_reports"):
                os.rmdir("test_reports")

    def test_start_new_severity_evaluation(self):
        financial_val = random.randint(5000, 500000)
        config = {
            "financial_index": financial_val,
            "severity_level": "HIGH"
        }

        result = start_new(config)
        self.assertIsNotNone(result)

    def test_start_new_anomaly_detection(self):
        anomaly_id = f"sig-{uuid.uuid4()}"
        config = {
            "anomaly_signature": anomaly_id
        }

        result = start_new(config)
        self.assertIsNotNone(result)

    def test_start_new_standard_incident_flow(self):
        incident_id = str(uuid.uuid4())
        log_path = f"/var/log/incident_{uuid.uuid4()}.log"
        telemetry_source = f"source_{uuid.uuid4()}"

        config = {
            "incident_id": incident_id,
            "log_path": log_path,
            "telemetry_source": telemetry_source
        }

        result = start_new(config)
        expected_message = f"Incident {incident_id} processed with log {log_path}"
        self.assertEqual(result, expected_message)

if __name__ == "__main__":
    unittest.main()