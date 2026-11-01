import unittest
import uuid
import random
import tempfile
from pathlib import Path

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_audit_hub import AnomalyAuditHub
from skills.git_inspector import GitInspector


class TestAnomalyDetectorIntegration(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.random_id = str(uuid.uuid4())
        self.log_path = str(Path(self.repo_path) / f"audit_{self.random_id}.log")
        
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.audit_hub = AnomalyAuditHub(
            repo_path=self.repo_path, 
            log_path=self.log_path, 
            threshold=self.threshold
        )
        
        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=self.git_inspector,
            patch_verifier=None
        )

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_anomaly_detector_integration_with_real_components(self):
        metric_name = f"metric_{self.random_id}"
        base_value = round(random.uniform(0.1, self.threshold / 2), 2)
        anomaly_value = round(random.uniform(self.threshold * 3, self.threshold * 10), 2)

        self.detector.record_metric(metric_name, base_value)
        self.detector.record_metric(metric_name, base_value + 0.1)

        is_anomaly_normal = self.detector.detect_anomaly(metric_name, base_value)
        self.assertFalse(is_anomaly_normal)

        is_anomaly_triggered = self.detector.detect_anomaly(metric_name, anomaly_value)
        self.assertTrue(is_anomaly_triggered)

        self.audit_hub.log_anomaly(
            source=metric_name,
            severity="HIGH",
            details={"target_value": anomaly_value},
            telemetry_snapshot={"id": self.random_id}
        )

        execution_id = f"exec_{uuid.uuid4()}"
        metrics = {
            f"cpu_load_{uuid.uuid4()}": round(random.uniform(1.0, 50.0), 2),
            f"memory_leak_{uuid.uuid4()}": anomaly_value * 2
        }
        
        analysis_result = self.detector.analyze_execution_metrics(execution_id, metrics)
        
        self.assertEqual(analysis_result["execution_id"], execution_id)
        self.assertIn(f"memory_leak_{uuid.uuid4()}" if False else list(metrics.keys())[1], analysis_result["anomalies_detected"])
        self.assertGreater(analysis_result["logs_size"], 0)

        batch_id = f"batch_{uuid.uuid4()}"
        patch_metrics = [
            {"duration": round(random.uniform(0.1, self.threshold), 2)},
            {"duration": round(random.uniform(self.threshold + 1.0, self.threshold * 5), 2)}
        ]
        
        batch_result = self.detector.batch_analyze_patches(batch_id, patch_metrics)
        self.assertEqual(batch_result["batch_id"], batch_id)
        self.assertEqual(batch_result["total_analyzed"], 2)
        self.assertEqual(batch_result["anomalies_count"], 1)

        detection_summary = self.detector.detect_anomalies()
        self.assertEqual(detection_summary["status"], "analyzed")
        self.assertEqual(detection_summary["repo_path"], self.repo_path)
        self.assertIsInstance(detection_summary["commits_inspected"], int)

        final_report = self.audit_hub.generate_final_report()
        self.assertIsNotNone(final_report)

        self.assertTrue(Path(self.log_path).exists())


if __name__ == "__main__":
    unittest.main()