import unittest
import os
import json
import uuid
import random
from unittest.mock import patch
from skills.incident_forensic_reporter import start_new, incident_forensic_reporter
from skills.incident_aggregator import incident_aggregator
from skills.telemetry_processor import telemetry_processor
from skills.telemetry_streamer import telemetry_streamer
from skills.telemetry_anomaly_evaluator_core import telemetry_anomaly_evaluator_core
from skills.incident_severity_evaluator import incident_severity_evaluator

class TestIncidentForensicReporterIntegration(unittest.TestCase):

    def setUp(self):
        self.incident_id = str(uuid.uuid4())
        self.telemetry_source = f"telemetry_{uuid.uuid4()}.log"
        self.output_path = f"reports/report_{uuid.uuid4()}.json"

        with open(self.telemetry_source, "w", encoding="utf-8") as f:
            f.write(f"TEST TELEMETRY STREAM DATA {random.randint(1000, 9999)}")

    def tearDown(self):
        if os.path.exists(self.telemetry_source):
            os.remove(self.telemetry_source)
        if os.path.exists(self.output_path):
            os.remove(self.output_path)
            try:
                os.rmdir(os.path.dirname(self.output_path))
            except OSError:
                pass

    @patch("requests.post")
    def test_status_and_flow_integration(self, mock_post):
        mock_anomaly_score = round(random.uniform(0.1, 0.9), 2)
        mock_severity_level = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])

        mock_post.return_value.json.return_value = {
            "status": "received",
            "incident_id": self.incident_id
        }

        with patch("skills.incident_forensic_reporter.incident_aggregator") as agg_mock, \
             patch("skills.incident_forensic_reporter.telemetry_streamer") as stream_mock, \
             patch("skills.incident_forensic_reporter.telemetry_processor") as proc_mock, \
             patch("skills.incident_forensic_reporter.telemetry_anomaly_evaluator_core") as anom_mock, \
             patch("skills.incident_forensic_reporter.incident_severity_evaluator") as sev_mock:

            expected_logs = {"log_id": str(uuid.uuid4()), "entries": random.randint(5, 50)}
            agg_mock.return_value = expected_logs
            stream_mock.return_value = None
            proc_mock.return_value = None
            anom_mock.return_value = {"anomaly_score": mock_anomaly_score}
            sev_mock.return_value = mock_severity_level

            result = start_new(
                incident_id=self.incident_id,
                telemetry_source=self.telemetry_source,
                evaluate_anomalies=True
            )

            self.assertEqual(result.get("incident_id"), self.incident_id)
            self.assertEqual(result.get("anomaly_score"), mock_anomaly_score)
            self.assertEqual(result.get("severity"), mock_severity_level)

        config = {
            "incident_data": {
                "incident_id": self.incident_id,
                "score": mock_anomaly_score,
                "severity": mock_severity_level
            },
            "output_path": self.output_path
        }

        report_result = incident_forensic_reporter(config)

        self.assertEqual(report_result.get("report_status"), "SUCCESS")
        self.assertEqual(report_result.get("target_incident_id"), self.incident_id)
        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("target_incident_id"), self.incident_id)
        self.assertEqual(file_data.get("details").get("severity"), mock_severity_level)

if __name__ == "__main__":
    unittest.main()
