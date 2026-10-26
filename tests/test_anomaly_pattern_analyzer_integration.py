import unittest
import os
import json
import uuid
import random
from skills.anomaly_pattern_analyzer import anomaly_filter, AnomalyAuditHub, AnomalyLogger

class TestAnomalyPatternAnalyzerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_id = str(uuid.uuid4())
        self.log_path = os.path.join("logs", f"test_anomaly_log_{self.test_id}.json")
        self.repo_path = os.path.join("repos", f"test_repo_{self.test_id}")
        self.metric_name = f"metric_{random.randint(1000, 9999)}"
        self.metric_value = random.uniform(1.0, 100.0)

    def tearDown(self):
        if os.path.exists(self.log_path):
            try:
                os.remove(self.log_path)
            except OSError:
                pass
        if os.path.exists(os.path.dirname(self.log_path)):
            try:
                os.rmdir(os.path.dirname(self.log_path))
            except OSError:
                pass

    def test_end_to_end_anomaly_workflow(self):
        random_source = f"source_{uuid.uuid4()}"
        random_severity = random.choice(["LOW", "MEDIUM", "HIGH", "CRITICAL"])
        random_details = f"Detailed error description {uuid.uuid4()}"
        random_telemetry = {"cpu_load": random.randint(0, 100), "memory_usage": random.random()}

        filter_input = {
            "source": random_source,
            "severity": random_severity,
            "details": random_details,
            "telemetry": random_telemetry
        }

        filtered_result = anomaly_filter.start_new(filter_input)

        self.assertEqual(filtered_result["status"], "processed")
        self.assertEqual(filtered_result["filtered_data"], filter_input)

        audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=random.randint(5, 50)
        )

        audit_hub.log_anomaly(
            source=filtered_result["filtered_data"]["source"],
            severity=filtered_result["filtered_data"]["severity"],
            details=filtered_result["filtered_data"]["details"],
            telemetry_snapshot=filtered_result["filtered_data"]["telemetry"]
        )

        audit_hub.aggregate_and_report(self.metric_name, self.metric_value)
        final_report = audit_hub.generate_final_report()
        self.assertEqual(final_report.get("status"), "success")

        logger = AnomalyLogger(log_path=self.log_path)
        anomalies = logger.get_anomalies()

        self.assertTrue(len(anomalies) > 0)

        found_match = False
        for anomaly in anomalies:
            if anomaly.get("details") == random_details:
                found_match = True
                self.assertEqual(anomaly.get("source"), random_source)
                self.assertEqual(anomaly.get("severity"), random_severity)
                self.assertEqual(anomaly.get("telemetry_snapshot"), random_telemetry)
                break

        self.assertTrue(found_match, "Logged anomaly with random details not found via AnomalyLogger.")

        structured_report = logger.get_structured_report()
        self.assertTrue(structured_report.get("structured"))
        self.assertIn("anomalies", structured_report)
        self.assertGreaterEqual(len(structured_report["anomalies"]), 1)

if __name__ == "__main__":
    unittest.main()