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
        self.log_path = os.path.join(self.temp_dir.name, f"audit_{uuid.uuid4()}.log")
        self.repo_path = self.temp_dir.name
        self.threshold = round(random.uniform(10.0, 99.9), 2)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_end_to_end_pipeline_and_logging(self):
        unique_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        random_value = round(random.uniform(100.0, 1000.0), 2)

        audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path,
            log_path=self.log_path,
            threshold=self.threshold
        )
        
        pipeline = AnomalyPipeline(
            repo_path=self.repo_path,
            threshold=self.threshold
        )

        raw_payload = {unique_metric_name: random_value}
        execution_id = str(uuid.uuid4())

        run_result = pipeline.run_end_to_end(execution_id, raw_payload)
        
        self.assertIsInstance(run_result, dict)
        self.assertIn(unique_metric_name, run_result)

        is_anom = run_result[unique_metric_name]
        
        if is_anom:
            audit_hub.log_anomaly(
                source="AnomalyPipelineIntegrationTest",
                severity="HIGH",
                details=f"Detected anomaly for metric {unique_metric_name} with value {random_value}",
                telemetry_snapshot={"execution_id": execution_id}
            )

        report = audit_hub.generate_final_report()

        logger = AnomalyLogger(log_path=self.log_path)
        logged_anomalies = logger.get_anomalies()

        self.assertTrue(os.path.exists(self.log_path), "Integration failed: Log file was not created.")
        self.assertIsNotNone(report)
        self.assertIsInstance(logged_anomalies, (list, dict))

    def test_pipeline_batch_processing_error_resilience(self):
        metric_count = random.randint(2, 5)
        payload = {f"metric_{uuid.uuid4().hex[:6]}": random.randint(1, 500) for _ in range(metric_count)}

        pipeline = AnomalyPipeline(
            repo_path=self.repo_path,
            threshold=self.threshold
        )

        batch_results = pipeline.run_batch(payload)
        self.assertIsInstance(batch_results, dict)

        processed_process = pipeline.process_pipeline(payload)
        self.assertIn("filtered_data", processed_process)
        self.assertIn("detection_result", processed_process)


if __name__ == "__main__":
    unittest.main()