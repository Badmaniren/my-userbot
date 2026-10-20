import unittest
import uuid
import random
from skills.anomaly_pipeline import AnomalyPipeline, AnomalyPipelineError
from skills.anomaly_logger import AnomalyLogger
from skills.anomaly_audit_hub import AnomalyAuditHub


class TestAnomalyPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.log_path = f"test_logs_{uuid.uuid4().hex}.json"
        self.repo_path = f"test_repo_{uuid.uuid4().hex}"
        self.threshold = random.uniform(50.0, 100.0)
        
        self.logger = AnomalyLogger(log_path=self.log_path)
        self.audit_hub = AnomalyAuditHub(repo_path=self.repo_path, log_path=self.log_path, threshold=self.threshold)
        self.pipeline = AnomalyPipeline(repo_path=self.repo_path, threshold=self.threshold)

    def tearDown(self):
        try:
            self.logger.clear_logs()
        except Exception:
            pass

    def test_pipeline_flow_with_real_components(self):
        metric_name = f"cpu_load_{uuid.uuid4().hex[:6]}"
        target_value = random.uniform(0.0, 150.0)

        raw_input = {metric_name: target_value}

        result = self.pipeline.run(raw_input)
        
        self.assertIn("is_anomaly", result)
        self.assertIn("metric_name", result)
        self.assertIn("target_value", result)
        
        self.assertEqual(result["metric_name"], metric_name)
        self.assertEqual(result["target_value"], target_value)
        
        if result["is_anomaly"]:
            self.audit_hub.log_anomaly(
                source="pipeline_integration_test",
                severity="HIGH",
                details=result,
                telemetry_snapshot={"metric": metric_name, "value": target_value}
            )

            logs = self.logger.get_anomalies()
            self.assertIsInstance(logs, (list, dict))

    def test_pipeline_batch_execution_randomized(self):
        metrics_count = random.randint(2, 5)
        raw_batch = {
            f"metric_{uuid.uuid4().hex[:4]}": random.uniform(10.0, 200.0)
            for _ in range(metrics_count)
        }

        batch_results = self.pipeline.run_batch(raw_batch)
        self.assertIsInstance(batch_results, dict)
        
        for m_name, is_anom in batch_results.items():
            self.assertIn(m_name, raw_batch)
            self.assertIsInstance(is_anom, bool)

            if is_anom:
                self.audit_hub.aggregate_and_report(m_name, raw_batch[m_name])

    def test_pipeline_flow_with_structured_event_data(self):
        metric_name = f"memory_usage_{uuid.uuid4().hex[:6]}"
        target_value = random.uniform(10.0, 100.0)
        
        raw_event = {
            "source": "integration_test",
            "severity": "HIGH",
            "details": "High memory usage detected",
            "telemetry_snapshot": {metric_name: target_value}
        }

        result = self.pipeline.run(raw_event)
        self.assertIn("is_anomaly", result)
        self.assertEqual(result["metric_name"], metric_name)
        self.assertEqual(result["target_value"], target_value)


if __name__ == "__main__":
    unittest.main()