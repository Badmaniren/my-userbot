import unittest
import os
import uuid
import random
import tempfile
from skills.anomaly_pipeline import AnomalyPipeline
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.anomaly_logger import AnomalyLogger

class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.log_path = os.path.join(self.test_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.test_dir.name
        self.threshold = random.uniform(50.0, 100.0)
        
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_pipeline_audit_logger_integration(self):
        execution_id = str(uuid.uuid4())
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        anomaly_value = random.uniform(self.threshold + 1.0, self.threshold + 50.0)
        
        payload = {metric_name: anomaly_value}
        
        pipeline_results = self.pipeline.run_end_to_end(execution_id, payload)
        self.assertIn(metric_name, pipeline_results)
        
        if pipeline_results[metric_name]:
            self.audit_hub.log_anomaly(
                source=execution_id,
                severity="HIGH",
                details={"metric": metric_name, "value": anomaly_value},
                telemetry_snapshot={"status": "active"}
            )
        
        logged_anomalies = self.logger.get_anomalies()
        self.assertIsInstance(logged_anomalies, list)
        
        report = self.logger.get_structured_report()
        self.assertIsNotNone(report)

if __name__ == "__main__":
    unittest.main()