import unittest
import uuid
import random
from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_filter import start_new

class TestAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/test_repo_{uuid.uuid4().hex}"
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        self.detector = AnomalyDetector(repo_path=self.repo_path, threshold=self.threshold)

    def test_anomaly_detection_integration_pipeline(self):
        metric_name = f"cpu_load_{uuid.uuid4().hex[:6]}"
        base_value = round(random.uniform(0.1, self.threshold), 2)

        self.detector.record_metric(metric_name, base_value)

        history = self.detector.get_metric_history(metric_name)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0], base_value)

        normal_target = round(base_value + random.uniform(0.0, 0.1), 2)
        is_anomaly_normal = self.detector.detect_anomaly(metric_name, normal_target)
        self.assertFalse(is_anomaly_normal)

        raw_data = {
            "metric": metric_name,
            "value": round(self.threshold * 10 + random.uniform(5.0, 20.0), 2),
            "token": uuid.uuid4().hex
        }

        filtered_result = start_new(raw_data)
        self.assertIsNotNone(filtered_result)

        anomaly_target = raw_data["value"]
        self.detector.record_metric(metric_name, anomaly_target)

        is_anomaly_high = self.detector.detect_anomaly(metric_name, anomaly_target)
        self.assertTrue(is_anomaly_high)

        execution_id = uuid.uuid4().hex
        metrics_payload = {
            metric_name: anomaly_target,
            f"latency_{uuid.uuid4().hex[:4]}": round(random.uniform(0.0, 1.0), 2)
        }

        analysis_result = self.detector.analyze_execution_metrics(execution_id, metrics_payload)
        self.assertEqual(analysis_result["execution_id"], execution_id)
        self.assertIn(metric_name, analysis_result["anomalies_detected"])
        self.assertGreater(analysis_result["logs_size"], 0)

        batch_id = uuid.uuid4().hex
        patch_metrics_list = [
            {"duration": round(self.threshold + random.uniform(1.0, 5.0), 2)},
            {"duration": round(self.threshold - random.uniform(0.1, 0.5), 2)}
        ]

        batch_result = self.detector.batch_analyze_patches(batch_id, patch_metrics_list)
        self.assertEqual(batch_result["batch_id"], batch_id)
        self.assertEqual(batch_result["total_analyzed"], 2)
        self.assertGreaterEqual(batch_result["anomalies_count"], 1)

        repo_analysis = self.detector.detect_anomalies()
        self.assertEqual(repo_analysis["status"], "analyzed")
        self.assertEqual(repo_analysis["repo_path"], self.repo_path)
        self.assertIsInstance(repo_analysis["anomalies_found"], list)

if __name__ == "__main__":
    unittest.main()