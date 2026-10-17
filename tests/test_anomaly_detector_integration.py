import unittest
import uuid
import random
import tempfile
from pathlib import Path

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError
from skills.anomaly_filter import start_new
from skills.git_inspector import GitInspector
from skills.patch_verifier import *

class TestAnomalyDetectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.threshold = round(random.uniform(1.0, 10.0), 2)

        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.patch_verifier = None

        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_integration_anomaly_filtering_and_detection_loop(self):
        execution_id = str(uuid.uuid4())
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"

        raw_data = [
            round(random.uniform(0.1, self.threshold), 2),
            round(random.uniform(self.threshold + 1.0, self.threshold * 10), 2),
            round(random.uniform(0.1, self.threshold), 2)
        ]

        filtered_result = start_new(raw_data)
        self.assertIsNotNone(filtered_result)

        for val in raw_data:
            self.detector.record_metric(metric_name, val)

        history = self.detector.get_metric_history(metric_name)
        self.assertEqual(len(history), len(raw_data))

        target_anomaly_value = self.threshold * 6.0
        is_anomaly = self.detector.detect_anomaly(metric_name, target_anomaly_value)
        self.assertTrue(is_anomaly)

        metrics_dict = {metric_name: target_anomaly_value}
        analysis_result = self.detector.analyze_execution_metrics(execution_id, metrics_dict)

        self.assertEqual(analysis_result["execution_id"], execution_id)
        self.assertIn(metric_name, analysis_result["anomalies_detected"])
        self.assertGreater(analysis_result["logs_size"], 0)

        batch_id = str(uuid.uuid4())
        patch_metrics = [
            {"duration": round(random.uniform(0.1, self.threshold / 2), 2)},
            {"duration": round(random.uniform(self.threshold + 2.0, self.threshold * 3), 2)}
        ]
        batch_result = self.detector.batch_analyze_patches(batch_id, patch_metrics)

        self.assertEqual(batch_result["batch_id"], batch_id)
        self.assertEqual(batch_result["total_analyzed"], 2)
        self.assertGreaterEqual(batch_result["anomalies_count"], 0)

        repo_analysis = self.detector.detect_anomalies()
        self.assertEqual(repo_analysis["status"], "analyzed")
        self.assertEqual(repo_analysis["repo_path"], self.repo_path)
        self.assertIn("commits_inspected", repo_analysis)

if __name__ == "__main__":
    unittest.main()