import unittest
from unittest.mock import MagicMock, patch
import uuid
import random
import io
import json
from skills.patch_optimizer import PatchOptimizer, PatchOptimizerError

class TestPatchOptimizer(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.anomaly_detector = MagicMock()
        self.system_telemetry = MagicMock()
        self.optimizer = PatchOptimizer(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )

    def test_init_sets_attributes(self):
        self.assertEqual(self.optimizer.repo_path, self.repo_path)
        self.assertEqual(self.optimizer.anomaly_detector, self.anomaly_detector)
        self.assertEqual(self.optimizer.system_telemetry, self.system_telemetry)

    def test_optimize_patch_success(self):
        patch_id = uuid.uuid4().hex
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_value = random.uniform(1.0, 100.0)
        patch_data = {
            "id": patch_id,
            "metric": metric_name,
            "target_value": target_value,
            "content": uuid.uuid4().hex
        }

        self.anomaly_detector.detect_anomaly.return_value = False
        self.system_telemetry.get_metric_history.return_value = [random.uniform(0, 10) for _ in range(5)]

        optimized = self.optimizer.optimize_patch(patch_data)

        self.assertIsInstance(optimized, dict)
        self.assertEqual(optimized["id"], patch_id)
        self.assertIn("optimized_score", optimized)
        self.anomaly_detector.detect_anomaly.assert_called_once_with(metric_name, target_value)

    def test_optimize_patch_raises_error_on_anomaly(self):
        patch_id = uuid.uuid4().hex
        metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        target_value = random.uniform(100.0, 1000.0)
        patch_data = {
            "id": patch_id,
            "metric": metric_name,
            "target_value": target_value,
            "content": uuid.uuid4().hex
        }

        self.anomaly_detector.detect_anomaly.return_value = True

        with self.assertRaises(PatchOptimizerError):
            self.optimizer.optimize_patch(patch_data)

    def test_prioritize_patches(self):
        patches = [
            {"id": uuid.uuid4().hex, "weight": random.randint(1, 10)},
            {"id": uuid.uuid4().hex, "weight": random.randint(11, 20)},
            {"id": uuid.uuid4().hex, "weight": random.randint(21, 30)}
        ]

        with patch.object(self.optimizer, 'optimize_patch', side_effect=lambda p: {**p, "optimized_score": p["weight"] * 1.5}):
            prioritized = self.optimizer.prioritize_patches(patches)

        self.assertEqual(len(prioritized), 3)
        self.assertTrue(prioritized[0]["optimized_score"] >= prioritized[1]["optimized_score"])
        self.assertTrue(prioritized[1]["optimized_score"] >= prioritized[2]["optimized_score"])

    def test_analyze_patch_history(self):
        history_id = uuid.uuid4().hex
        mock_history = [
            {"patch_id": uuid.uuid4().hex, "success": True, "latency": random.uniform(0.1, 5.0)},
            {"patch_id": uuid.uuid4().hex, "success": False, "latency": random.uniform(5.0, 10.0)}
        ]
        self.system_telemetry.export_stream.return_value = mock_history

        analysis = self.optimizer.analyze_patch_history(history_id)

        self.assertIsInstance(analysis, dict)
        self.assertIn("success_rate", analysis)
        self.assertEqual(analysis["total_analyzed"], 2)

    def test_export_optimization_report(self):
        report_id = uuid.uuid4().hex
        mock_data = io.BytesIO(json.dumps({str(uuid.uuid4()): random.random()} ).encode('utf-8'))

        with patch('builtins.open', create=True) as mock_open:
            mock_open.return_value.__enter__.return_value.read.return_value = mock_data.read()
            report = self.optimizer.export_optimization_report(report_id)

        self.assertIsInstance(report, dict)

    def test_optimize_patch_with_io_exception(self):
        patch_id = uuid.uuid4().hex
        patch_data = {"id": patch_id, "content": uuid.uuid4().hex}
        self.anomaly_detector.detect_anomaly.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(PatchOptimizerError):
            self.optimizer.optimize_patch(patch_data)