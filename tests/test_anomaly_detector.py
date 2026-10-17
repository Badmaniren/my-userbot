import unittest
from unittest.mock import patch, MagicMock
import io
import os
import random
import uuid
from pathlib import Path
from typing import Dict, List, Any, Optional

from skills.anomaly_detector import AnomalyDetector, AnomalyDetectorError

class TestAnomalyDetectorInquisition(unittest.TestCase):
    def setUp(self) -> str:
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.threshold = round(random.uniform(1.0, 10.0), 2)
        self.detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold
        )

    def test_record_and_get_metric_history(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        val1 = round(random.uniform(0.1, 50.0), 2)
        val2 = round(random.uniform(51.0, 100.0), 2)

        self.detector.record_metric(metric_name, val1)
        self.detector.record_metric(metric_name, val2)

        history = self.detector.get_metric_history(metric_name)
        self.assertEqual(history, [val1, val2])

    def test_detect_anomaly_no_history(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_val = round(random.uniform(10.0, 100.0), 2)

        with self.assertRaises(AnomalyDetectorError):
            self.detector.detect_anomaly(metric_name, target_val)

    def test_detect_anomaly_true_and_false(self) -> None:
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        for _ in range(5):
            self.detector.record_metric(metric_name, 10.0)

        anomaly_val = 10.0 + self.threshold + round(random.uniform(1.0, 10.0), 2)
        self.assertTrue(self.detector.detect_anomaly(metric_name, anomaly_val))

        normal_val = 10.0
        self.assertFalse(self.detector.detect_anomaly(metric_name, normal_val))

    def test_analyze_execution_metrics(self) -> None:
        execution_id = uuid.uuid4().hex
        metric_name = f"exec_metric_{uuid.uuid4().hex[:6]}"
        high_val = self.threshold * 5 + round(random.uniform(1.0, 10.0), 2)
        metrics = {metric_name: high_val}

        result = self.detector.analyze_execution_metrics(execution_id, metrics)
        self.assertEqual(result["execution_id"], execution_id)
        self.assertIn(metric_name, result["anomalies_detected"])
        self.assertGreater(result["logs_size"], 0)

    def test_batch_analyze_patches(self) -> None:
        batch_id = uuid.uuid4().hex
        p_name = f"patch_{uuid.uuid4().hex[:6]}"
        duration_anomaly = self.threshold + round(random.uniform(1.0, 5.0), 2)
        duration_normal = max(0.1, self.threshold - round(random.uniform(0.1, 1.0), 2))

        patch_metrics = [
            {"patch_id": p_name, "duration": duration_anomaly},
            {"patch_id": f"patch_{uuid.uuid4().hex[:6]}", "duration": duration_normal}
        ]

        result = self.detector.batch_analyze_patches(batch_id, patch_metrics)
        self.assertEqual(result["batch_id"], batch_id)
        self.assertEqual(result["total_analyzed"], 2)
        self.assertEqual(result["anomalies_count"], 1)

    def test_detect_anomalies_with_git_inspector(self) -> None:
        mock_git = MagicMock()
        commit_hash = uuid.uuid4().hex
        mock_git.get_commit_history.return_value = [{"hash": commit_hash}]

        detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=mock_git
        )

        res = detector.detect_anomalies()
        self.assertEqual(res["status"], "analyzed")
        self.assertEqual(res["repo_path"], self.repo_path)
        self.assertEqual(res["commits_inspected"], 1)

    def test_detect_anomalies_git_inspector_exception(self) -> None:
        mock_git = MagicMock()
        mock_git.get_commit_history.side_effect = Exception(uuid.uuid4().hex)

        detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=self.threshold,
            git_inspector=mock_git
        )

        res = detector.detect_anomalies()
        self.assertEqual(res["commits_inspected"], 0)

    def test_primary_analysis_contour_integration_mocked(self) -> None:
        raw_values = [round(random.uniform(1.0, 100.0), 2) for _ in range(3)]
        metric_name = f"integration_metric_{uuid.uuid4().hex[:6]}"

        with patch("skills.anomaly_filter.start_new") as mock_filter:
            filtered_mock_data = {f"val_{uuid.uuid4().hex[:4]}": raw_values[0]}
            mock_filter.return_value = filtered_mock_data

            for val in raw_values:
                self.detector.record_metric(metric_name, val)

            history = self.detector.get_metric_history(metric_name)
            self.assertEqual(len(history), 3)