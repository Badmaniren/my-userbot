import unittest
import uuid
import random
import os
import tempfile
from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.log_file = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(50.0, 99.9), 2)

        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_file,
            threshold=self.threshold
        )
        self.logger = AnomalyLogger(log_path=self.log_file)
        self.pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_pipeline_end_to_end_audit_and_logging_integration(self):
        metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = round(random.uniform(self.threshold + 1.0, self.threshold + 50.0), 2)
        
        raw_payload = {metric_key: metric_value}
        execution_id = str(uuid.uuid4())

        run_result = self.pipeline.run_end_to_end(execution_id, raw_payload)
        
        self.assertIn(metric_key, run_result)
        self.assertTrue(run_result[metric_key])

        severity_level = "CRITICAL"
        details_msg = f"Integration test anomaly for execution {execution_id}"
        telemetry_data = {"cpu_load": round(random.uniform(10.0, 99.9), 2)}

        self.audit_hub.log_anomaly(
            source=metric_key,
            severity=severity_level,
            details=details_msg,
            telemetry_snapshot=telemetry_data
        )

        logged_anomalies = self.logger.get_anomalies()
        self.assertIsInstance(logged_anomalies, list)
        self.assertGreaterEqual(len(logged_anomalies), 1)

        found_log = False
        for entry in logged_anomalies:
            if isinstance(entry, dict) and entry.get("source") == metric_key:
                found_log = True
                self.assertEqual(entry.get("severity"), severity_level)
                self.assertEqual(entry.get("details"), details_msg)
                break
            elif isinstance(entry, str) and metric_key in entry:
                found_log = True
                break

        self.assertTrue(found_log, "Log entry from AnomalyAuditHub was not found in AnomalyLogger records.")

        report = self.logger.get_structured_report()
        self.assertIsNotNone(report)

        self.assertTrue(os.path.exists(self.log_file))

if __name__ == "__main__":
    unittest.main()