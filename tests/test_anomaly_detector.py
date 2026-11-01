import unittest
from unittest.mock import MagicMock, patch
import io
import os
import random
import uuid
from pathlib import Path

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError

class TestAnomalyDetector(unittest.TestCase):

    def setUp(self) -> str:
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.threshold = random.uniform(1.0, 10.0)
        self.git_inspector_mock = MagicMock()
        self.patch_verifier_mock = MagicMock()
        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=self.git_inspector_mock,
            patch_verifier=self.patch_verifier_mock
        )

    def test_record_metric_and_get_history(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        values = [random.uniform(0.0, 50.0) for _ in range(5)]

        for val in values:
            self.detector.record_metric(metric_name, val)

        history = self.detector.get_metric_history(metric_name)
        self.assertEqual(history, values)
        self.assertEqual(self.detector.history, values)

    def test_get_metric_history_non_existent(self) -> None:
        non_existent = f"metric_{uuid.uuid4().hex[:8]}"
        history = self.detector.get_metric_history(non_existent)
        self.assertEqual(history, [])

    def test_detect_anomaly_raises_error_when_no_history(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        target = random.uniform(10.0, 100.0)

        with self.assertRaises(AnomalyDetectorError):
            self.detector.detect_anomaly(metric_name, target)

    def test_detect_anomaly_returns_true_on_threshold_exceed(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.detector.record_metric(metric_name, 1.0)
        self.detector.record_metric(metric_name, 2.0)

        high_target = self.threshold * 3.0
        is_anomaly = self.detector.detect_anomaly(metric_name, high_target)
        self.assertTrue(is_anomaly)

    def test_detect_anomaly_returns_false_within_normal_range(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        base_val = 1.0
        for _ in range(3):
            self.detector.record_metric(metric_name, base_val)

        normal_target = base_val + (self.threshold * 0.1)
        is_anomaly = self.detector.detect_anomaly(metric_name, normal_target)
        self.assertFalse(is_anomaly)

    def test_fetch_execution_logs(self) -> None:
        exec_id = uuid.uuid4().hex
        logs_stream = self.detector._fetch_execution_logs(exec_id)
        self.assertIsInstance(logs_stream, io.BytesIO)
        content = logs_stream.getvalue().decode('utf-8')
        self.assertIn(exec_id, content)

    def test_analyze_execution_metrics(self) -> None:
        exec_id = uuid.uuid4().hex
        metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        extreme_value = self.threshold * 6.0
        metrics = {metric_key: extreme_value}

        with patch.object(self.detector, '_fetch_execution_logs', return_value=io.BytesIO(uuid.uuid4().hex.encode('utf-8'))):
            result = self.detector.analyze_execution_metrics(exec_id, metrics)

        self.assertEqual(result["execution_id"], exec_id)
        self.assertIn(metric_key, result["anomalies_detected"])
        self.assertGreater(result["logs_size"], 0)
        self.assertEqual(self.detector.get_metric_history(metric_key), [extreme_value])

    def test_batch_analyze_patches(self) -> None:
        batch_id = uuid.uuid4().hex
        patch_metrics = [
            {"duration": self.threshold + random.uniform(1.0, 10.0)},
            {"duration": self.threshold * 0.1}
        ]

        result = self.detector.batch_analyze_patches(batch_id, patch_metrics)

        self.assertEqual(result["batch_id"], batch_id)
        self.assertEqual(result["total_analyzed"], 2)
        self.assertEqual(result["anomalies_count"], 1)

    def test_detect_anomalies_with_git_inspector(self) -> None:
        commit_list = [uuid.uuid4().hex, uuid.uuid4().hex]
        self.git_inspector_mock.get_commit_history.return_value = commit_list

        result = self.detector.detect_anomalies()

        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["commits_inspected"], len(commit_list))
        self.assertEqual(result["anomalies_found"], [])
        self.git_inspector_mock.get_commit_history.assert_called_once_with(max_count=10)

    def test_detect_anomalies_git_inspector_exception_handling(self) -> None:
        self.git_inspector_mock.get_commit_history.side_effect = Exception(uuid.uuid4().hex)

        result = self.detector.detect_anomalies()

        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["commits_inspected"], 0)
        self.assertEqual(result["anomalies_found"], [])

    def test_detect_anomalies_without_git_inspector(self) -> None:
        detector_no_git = AnomalyDetector(repo_path=self.repo_path, threshold=self.threshold)
        result = detector_no_git.detect_anomalies()

        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["commits_inspected"], 0)
        self.assertEqual(result["anomalies_found"], [])

if __name__ == '__main__':
    unittest.main()