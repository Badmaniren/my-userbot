import unittest
from unittest.mock import MagicMock, patch
import io
import uuid
import random
import string

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError

class TestAnomalyDetector(unittest.TestCase):

    def setUp(self) -> None:
        self.repo_path = f"/repo/{uuid.uuid4().hex}"
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold
        )

    def test_init_sets_attributes(self) -> None:
        custom_repo = f"/path/{uuid.uuid4().hex}"
        custom_threshold = round(random.uniform(2.0, 8.0), 2)
        mock_git = MagicMock()
        mock_verifier = MagicMock()

        detector = AnomalyDetector(
            repo_path=custom_repo,
            threshold=custom_threshold,
            git_inspector=mock_git,
            patch_verifier=mock_verifier
        )

        self.assertEqual(detector.repo_path, custom_repo)
        self.assertEqual(detector.threshold, custom_threshold)
        self.assertEqual(detector.git_inspector, mock_git)
        self.assertEqual(detector.patch_verifier, mock_verifier)
        self.assertEqual(detector.history, [])
        self.assertEqual(detector._metric_history_dict, {})

    def test_record_metric_stores_value(self) -> None:
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        value = round(random.uniform(10.0, 100.0), 2)

        self.detector.record_metric(metric_name, value)

        self.assertIn(value, self.detector.history)
        self.assertEqual(self.detector.get_metric_history(metric_name), [value])

        another_value = round(random.uniform(1.0, 9.0), 2)
        self.detector.record_metric(metric_name, another_value)
        self.assertEqual(self.detector.get_metric_history(metric_name), [value, another_value])

    def test_get_metric_history_empty(self) -> None:
        non_existent_metric = ''.join(random.choices(string.ascii_lowercase, k=10))
        history = self.detector.get_metric_history(non_existent_metric)
        self.assertEqual(history, [])

    def test_detect_anomaly_raises_error_when_no_history(self) -> None:
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=7))
        target_value = round(random.uniform(50.0, 150.0), 2)

        with self.assertRaises(AnomalyDetectorError):
            self.detector.detect_anomaly(metric_name, target_value)

    def test_detect_anomaly_true_and_false(self) -> None:
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=6))
        base_val = 10.0
        self.detector.threshold = 5.0
        
        self.detector.record_metric(metric_name, base_val)
        self.detector.record_metric(metric_name, base_val)

        normal_target = 12.0
        self.assertFalse(self.detector.detect_anomaly(metric_name, normal_target))

        anomaly_by_diff = base_val + self.detector.threshold + 1.0
        self.assertTrue(self.detector.detect_anomaly(metric_name, anomaly_by_diff))

        anomaly_by_scale = self.detector.threshold * 2 + 1.0
        self.assertTrue(self.detector.detect_anomaly(metric_name, anomaly_by_scale))

    def test_fetch_execution_logs(self) -> None:
        exec_id = uuid.uuid4().hex
        log_stream = self.detector._fetch_execution_logs(exec_id)
        
        self.assertIsInstance(log_stream, io.BytesIO)
        content = log_stream.getvalue().decode('utf-8')
        self.assertIn(exec_id, content)

    def test_analyze_execution_metrics(self) -> None:
        exec_id = uuid.uuid4().hex
        metric_1 = ''.join(random.choices(string.ascii_lowercase, k=5))
        metric_2 = ''.join(random.choices(string.ascii_lowercase, k=6))
        
        high_val = self.detector.threshold * 5 + random.uniform(1.0, 10.0)
        low_val = round(random.uniform(0.1, 2.0), 2)

        metrics = {
            metric_1: high_val,
            metric_2: low_val
        }

        with patch.object(self.detector, '_fetch_execution_logs', return_value=io.BytesIO(b"random_logs_data")):
            result = self.detector.analyze_execution_metrics(exec_id, metrics)

        self.assertEqual(result["execution_id"], exec_id)
        self.assertIn(metric_1, result["anomalies_detected"])
        self.assertNotIn(metric_2, result["anomalies_detected"])
        self.assertGreater(result["logs_size"], 0)
        self.assertEqual(self.detector.get_metric_history(metric_1), [high_val])
        self.assertEqual(self.detector.get_metric_history(metric_2), [low_val])

    def test_batch_analyze_patches(self) -> None:
        batch_id = uuid.uuid4().hex
        dur_1 = round(self.detector.threshold + random.uniform(1.0, 5.0), 2)
        dur_2 = round(self.detector.threshold - random.uniform(0.1, 2.0), 2)

        patch_metrics = [
            {"patch_id": uuid.uuid4().hex, "duration": dur_1},
            {"patch_id": uuid.uuid4().hex, "duration": dur_2}
        ]

        result = self.detector.batch_analyze_patches(batch_id, patch_metrics)

        self.assertEqual(result["batch_id"], batch_id)
        self.assertEqual(result["total_analyzed"], 2)
        self.assertEqual(result["anomalies_count"], 1)
        self.assertEqual(self.detector.get_metric_history("batch_duration"), [dur_1, dur_2])

    def test_detect_anomalies_with_git_inspector(self) -> None:
        mock_git = MagicMock()
        random_commits = [uuid.uuid4().hex for _ in range(random.randint(1, 5))]
        mock_git.get_commit_history.return_value = random_commits

        detector = AnomalyDetector(
            repo_path=self.repo_path,
            git_inspector=mock_git
        )

        result = detector.detect_anomalies()

        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["commits_inspected"], len(random_commits))
        self.assertEqual(result["anomalies_found"], [])
        mock_git.get_commit_history.assert_called_once_with(max_count=10)

    def test_detect_anomalies_git_inspector_exception(self) -> None:
        mock_git = MagicMock()
        mock_git.get_commit_history.side_effect = Exception("Git fail")

        detector = AnomalyDetector(
            repo_path=self.repo_path,
            git_inspector=mock_git
        )

        result = detector.detect_anomalies()

        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["commits_inspected"], 0)
        self.assertEqual(result["anomalies_found"], [])

    def test_detect_anomalies_without_git_inspector(self) -> None:
        result = self.detector.detect_anomalies()

        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["commits_inspected"], 0)
        self.assertEqual(result["anomalies_found"], [])

if __name__ == '__main__':
    unittest.main()