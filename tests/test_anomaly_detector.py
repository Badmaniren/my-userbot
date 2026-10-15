import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError

class TestAnomalyDetector(unittest.TestCase):
    
    def setUp(self):
        self.random_repo_path = f"/var/repo/{uuid.uuid4().hex}"
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.threshold = random.uniform(1.0, 10.0)
        self.detector = AnomalyDetector(repo_path=self.random_repo_path, threshold=self.threshold)

    def test_init_sets_attributes(self):
        self.assertEqual(self.detector.repo_path, self.random_repo_path)
        self.assertEqual(self.detector.threshold, self.threshold)
        self.assertIsInstance(self.detector.history, list)

    def test_detect_anomaly_normal_behavior(self):
        normal_values = [random.uniform(0.1, self.threshold) for _ in range(10)]
        target_value = random.uniform(0.1, self.threshold)
        
        for val in normal_values:
            self.detector.record_metric(self.metric_name, val)
            
        is_anomaly = self.detector.detect_anomaly(self.metric_name, target_value)
        self.assertFalse(is_anomaly)

    def test_detect_anomaly_triggered(self):
        normal_values = [random.uniform(0.1, 2.0) for _ in range(10)]
        for val in normal_values:
            self.detector.record_metric(self.metric_name, val)
            
        extreme_value = self.threshold + random.uniform(5.0, 50.0)
        is_anomaly = self.detector.detect_anomaly(self.metric_name, extreme_value)
        self.assertTrue(is_anomaly)

    def test_analyze_execution_metrics_returns_dict(self):
        execution_id = uuid.uuid4().hex
        mock_metrics = {
            f"cpu_usage_{uuid.uuid4().hex[:4]}": random.uniform(10, 90),
            f"memory_usage_{uuid.uuid4().hex[:4]}": random.uniform(100, 500)
        }
        
        with patch('skills.anomaly_detector.AnomalyDetector._fetch_execution_logs') as mock_fetch:
            mock_fetch.return_value = io.BytesIO(f"execution_id: {execution_id}".encode('utf-8'))
            result = self.detector.analyze_execution_metrics(execution_id, mock_metrics)
            
        self.assertIsInstance(result, dict)
        self.assertIn("anomalies_detected", result)
        self.assertIn("execution_id", result)
        self.assertEqual(result["execution_id"], execution_id)

    def test_custom_exception_inheritance(self):
        self.assertTrue(issubclass(AnomalyDetectorError, Exception))
        err_msg = "".join(random.choices(string.ascii_letters, k=15))
        with self.assertRaises(AnomalyDetectorError):
            raise AnomalyDetectorError(err_msg)

    def test_record_and_retrieve_history(self):
        metric_key = f"key_{uuid.uuid4().hex[:6]}"
        metric_val = random.uniform(5.0, 100.0)
        
        self.detector.record_metric(metric_key, metric_val)
        history = self.detector.get_metric_history(metric_key)
        
        self.assertIn(metric_VAL := metric_val, history)

    def test_analyze_empty_metric_raises_error(self):
        non_existent_metric = f"ghost_{uuid.uuid4().hex}"
        target = random.uniform(1.0, 10.0)
        
        with self.assertRaises(AnomalyDetectorError):
            self.detector.detect_anomaly(non_existent_metric, target)

    def test_batch_analyze_patches(self):
        batch_id = uuid.uuid4().hex
        patch_metrics = [
            {"patch_hash": uuid.uuid4().hex, "duration": random.uniform(0.1, 5.0)}
            for _ in range(random.randint(3, 8))
        ]
        
        analysis = self.detector.batch_analyze_patches(batch_id, patch_metrics)
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get("batch_id"), batch_id)
        self.assertIn("total_analyzed", analysis)
        self.assertEqual(analysis["total_analyzed"], len(patch_metrics))

if __name__ == '__main__':
    unittest.main()