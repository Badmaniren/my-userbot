import unittest
import uuid
import random
import os
import tempfile
from skills.incident_forensic_reporter import incident_forensic_reporter
from skills.incident_aggregator import incident_aggregator
from skills.telemetry_processor import telemetry_processor
from skills.incident_severity_evaluator import incident_severity_evaluator

class IntegrationTestIncidentForensicReporter(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.incident_id = str(uuid.uuid4())
        self.telemetry_source = f"source-{random.randint(1000, 9999)}"
        self.severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        self.error_code = random.randint(500, 599)

    def tearDown:
        for root, dirs, files in os.walk(self.test_dir, topdown=False):
            for name in files:
                os.remove(os.path.join(root, name))
            for name in dirs:
                os.rmdir(os.path.join(root, name))
        os.rmdir(self.test_dir)

    def test_incident_forensic_reporter_integration(self):
        raw_telemetry_data = {
            "event_id": str(uuid.uuid4()),
            "source": self.telemetry_source,
            "metric_value": random.uniform(10.0, 100.0),
            "status_code": self.error_code,
            "payload": f"random_payload_{random.random()}"
        }

        processed_telemetry = telemetry_processor(raw_telemetry_data)
        
        self.assertIsNotNone(processed_telemetry, "Telemetry processor returned None")

        severity_result = incident_severity_evaluator({
            "incident_id": self.incident_id,
            "telemetry": processed_telemetry,
            "base_severity": self.severity_level
        })

        self.assertEqual(severity_result.get("incident_id"), self.incident_id)

        aggregated_incident = incident_aggregator({
            "incident_id": self.incident_id,
            "severity_data": severity_result,
            "telemetry_stream": [processed_telemetry]
        })

        self.assertIn("incident_id", aggregated_incident)

        report_output_path = os.path.join(self.test_dir, f"report_{self.incident_id}.json")
        
        forensic_report = incident_forensic_reporter({
            "incident_data": aggregated_incident,
            "output_path": report_output_path,
            "include_raw_telemetry": True
        })

        self.assertTrue(os.path.exists(report_output_path), "Forensic report file was not created")
        
        self.assertEqual(forensic_report.get("report_status"), "SUCCESS")
        self.assertEqual(forensic_report.get("target_incident_id"), self.incident_id)

        with open(report_output_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.incident_id, content)
            self.assertIn(str(self.error_code), content)

if __name__ == "__main__":
    unittest.main()