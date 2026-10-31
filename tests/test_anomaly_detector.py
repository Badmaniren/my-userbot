import unittest
from unittest.mock import MagicMock, patch
import io
import random
import uuid
from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError

class TestAnomalyDetector(unittest.TestCase):
    def setUp(self) -> None:
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.threshold = random.uniform(1.0, 10.0)
        self.detector = AnomalyDetector(repo_path=self.repo_path, threshold=self.threshold)

    def test_init_state(self) -> None:
        self.assertEqual(self.detector.repo_path, self.repo_path)
        self.assertEqual(self.detector.threshold, self.threshold)
        self.assertIsNone(self.detector.git_inspector)
        self.assertIsNone(self.detector.patch_verifier)
        self.assertEqual(self.detector.history, [])
        self.assertEqual(self.detector._metric_history_dict, {})

    def test_record_metric_and_get_history(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        val1 = random.uniform(0.0, 50.0)
        val2 = random.uniform(51.0, 100.0)

        self.detector.record_metric(metric_name, val1)
        self.detector.record_metric(metric_name, val2)

        history = self.detector.get_metric_history(metric_name)
        self.assertEqual(history, [val1, val2])
        self.assertEqual(self.detector.history, [val1, val2])

        non_existent = f"metric_{uuid.uuid4().hex[:6]}"
        self.assertEqual(self.detector.get_metric_history(non_existent), [])

    def test_detect_anomaly_no_history(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_val = random.uniform(1.0, 100.0)
        with self.assertRaises(AnomalyDetectorError):
            self.detector.detect_anomaly(metric_name, target_val)

    def test_detect_anomaly_normal_and_abnormal(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        base_val = 10.0
        self.detector.record_metric(metric_name, base_val)
        self.detector.record_metric(metric_name, base_val)

        normal_val = base_val + (self.threshold / 2)
        self.assertFalse(self.detector.detect_anomaly(metric_name, normal_val))

        anomaly_val_diff = base_val + self.threshold + random.uniform(1.0, 10.0)
        self.assertTrue(self.detector.detect_anomaly(metric_name, anomaly_val_diff))

        anomaly_val_mult = (self.threshold * 2) + random.uniform(1.0, 10.0)
        self.assertTrue(self.detector.detect_anomaly(metric_name, anomaly_val_mult))

    def test_fetch_execution_logs(self) -> None:
        exec_id = uuid.uuid4().hex
        log_bytes = self.detector._fetch_execution_logs(exec_id)
        self.assertIsInstance(log_bytes, io.BytesIO)
        self.assertIn(exec_id.encode('utf-8'), log_bytes.getvalue())

    def test_analyze_execution_metrics(self) -> None:
        exec_id = uuid.uuid4().hex
        metric_name = f"exec_metric_{uuid.uuid4().hex[:6]}"
        high_val = self.threshold * 5 + random.uniform(1.0, 10.0)
        low_val = self.threshold

        metrics = {
            metric_name: high_val,
            f"other_{metric_name}": low_val
        }

        with patch.object(self.detector, '_fetch_execution_logs') as mock_fetch:
            random_log_data = uuid.uuid4().bytes
            mock_fetch.return_value = io.BytesIO(random_log_data)

            result = self.detector.analyze_execution_metrics(exec_id, metrics)

            self.assertEqual(result["execution_id"], exec_id)
            self.assertIn(metric_name, result["anomalies_detected"])
            self.assertNotIn(f"other_{metric_name}", result["anomalies_detected"])
            self.assertEqual(result["logs_size"], len(random_log_data))

    def test_batch_analyze_patches(self) -> None:
        batch_id = uuid.uuid4().hex
        dur1 = self.threshold + random.uniform(1.0, 5.0)
        dur2 = self.threshold - random.uniform(0.1, self.threshold if self.threshold > 0.1 else 0.05)
        
        patch_metrics = [
            {"duration": dur1},
            {"duration": dur2},
            {}
        ]

        result = self.detector.batch_analyze_patches(batch_id, patch_metrics)

        self.assertEqual(result["batch_id"], batch_id)
        self.assertEqual(result["total_analyzed"], 3)
        self.assertEqual(result["anomalies_count"], 1)

    def test_detect_anomalies_with_git_inspector(self) -> None:
        mock_inspector = MagicMock()
        commit_count = random.randint(1, 15)
        mock_inspector.get_commit_history.return_value = [uuid.uuid4().hex for _ in range(commit_count)]

        detector_with_git = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=mock_inspector
        )

        res = detector_with_git.detect_anomalies()
        self.assertEqual(res["status"], "analyzed")
        self.assertEqual(res["repo_path"], self.repo_path)
        self.assertEqual(res["commits_inspected"], commit_count)
        self.assertEqual(res["anomalies_found"], [])
        mock_inspector.get_commit_history.assert_called_once_with(max_count=10)

    def test_detect_anomalies_git_inspector_exception(self) -> None:
        mock_inspector = MagicMock()
        mock_inspector.get_commit_history.side_effect = Exception(uuid.uuid4().hex)

        detector_with_git = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=mock_inspector
        )

        res = detector_with_git.detect_anomalies()
        self.assertEqual(res["status"], "analyzed")
        self.assertEqual(res["commits_inspected"], 0)
        self.assertEqual(res["anomalies_found"], [])

    def test_detect_anomalies_without_git_inspector(self) -> None:
        res = self.detector.detect_anomalies()
        self.assertEqual(res["status"], "analyzed")
        self.assertEqual(res["commits_inspected"], 0)
        self.assertEqual(res["anomalies_found"], [])