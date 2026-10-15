import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
from pathlib import Path
import io

from skills.patch_scheduler import PatchScheduler, PatchSchedulerError

class TestPatchScheduler(unittest.TestCase):
    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.anomaly_detector = MagicMock()
        self.stability_digest = MagicMock()
        self.system_telemetry = MagicMock()

        self.scheduler = PatchScheduler(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            stability_digest=self.stability_digest,
            system_telemetry=self.system_telemetry
        )

    def test_schedule_patches_prioritization(self):
        exec_id = uuid.uuid4().hex
        critical_id = uuid.uuid4().hex
        medium_id = uuid.uuid4().hex
        low_id = uuid.uuid4().hex
        priority_id = uuid.uuid4().hex

        patches = [
            {"patch_id": low_id, "severity": "low"},
            {"patch_id": critical_id, "severity": "critical"},
            {"patch_id": priority_id, "priority": 10},
            {"patch_id": medium_id, "severity": "medium"}
        ]

        self.stability_digest.generate_digest.return_value = {"patches": patches}

        sorted_patches = self.scheduler.schedule_patches(exec_id)

        self.assertEqual(sorted_patches[0]["patch_id"], critical_id)
        self.assertEqual(sorted_patches[1]["patch_id"], priority_id)
        self.assertEqual(sorted_patches[2]["patch_id"], medium_id)
        self.assertEqual(sorted_patches[3]["patch_id"], low_id)

    def test_schedule_patches_raises_error(self):
        exec_id = uuid.uuid4().hex
        err_msg = uuid.uuid4().hex
        self.stability_digest.generate_digest.side_effect = Exception(err_msg)

        with self.assertRaises(PatchSchedulerError) as ctx:
            self.scheduler.schedule_patches(exec_id)
        self.assertIn(err_msg, str(ctx.exception))

    def test_prioritize_patches(self):
        p1_id = uuid.uuid4().hex
        p2_id = uuid.uuid4().hex
        patches = [
            {"patch_id": p1_id, "priority": random.randint(1, 50)},
            {"patch_id": p2_id, "priority": random.randint(51, 100)}
        ]

        prioritized = self.scheduler.prioritize_patches(patches)
        self.assertEqual(prioritized[0]["patch_id"], p2_id)
        self.assertEqual(prioritized[1]["patch_id"], p1_id)

    def test_prioritize_patches_empty(self):
        self.assertEqual(self.scheduler.prioritize_patches([]), [])

    def test_evaluate_patch_readiness_true(self):
        stream_id = uuid.uuid4().hex
        patch_data = {"patch_id": uuid.uuid4().hex}
        self.stability_digest.export_digest_stream.return_value = {
            "status": "stable",
            "score": float(random.randint(50, 100))
        }

        result = self.scheduler.evaluate_patch_readiness(patch_data, stream_id)
        self.assertTrue(result)

    def test_evaluate_patch_readiness_false(self):
        stream_id = uuid.uuid4().hex
        patch_data = {"patch_id": uuid.uuid4().hex}
        self.stability_digest.export_digest_stream.return_value = {
            "status": "unstable",
            "score": float(random.randint(0, 49))
        }

        result = self.scheduler.evaluate_patch_readiness(patch_data, stream_id)
        self.assertFalse(result)

    def test_evaluate_patch_readiness_no_digest(self):
        scheduler_no_digest = PatchScheduler(repo_path=self.repo_path)
        result = scheduler_no_digest.evaluate_patch_readiness({}, uuid.uuid4().hex)
        self.assertFalse(result)

    def test_export_schedule_stream_existing(self):
        stream_id = uuid.uuid4().hex
        expected_data = {"stream_id": stream_id, "status": uuid.uuid4().hex}
        json_content = json.dumps(expected_data)

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", unittest.mock.mock_open(read_data=json_content)):
                res = self.scheduler.export_schedule_stream(stream_id)
                self.assertEqual(res, expected_data)

    def test_export_schedule_stream_missing(self):
        stream_id = uuid.uuid4().hex
        with patch("pathlib.Path.exists", return_value=False):
            res = self.scheduler.export_schedule_stream(stream_id)
            self.assertEqual(res, {"stream_id": stream_id})

    def test_analyze_schedule_impact_with_detector(self):
        exec_id = uuid.uuid4().hex
        metric_name = uuid.uuid4().hex
        expected = {"anomaly_detected": True, "impact_score": random.random()}
        self.anomaly_detector.analyze_execution_metrics.return_value = expected

        res = self.scheduler.analyze_schedule_impact(exec_id, metric_name)
        self.assertEqual(res, expected)

    def test_analyze_schedule_impact_without_detector(self):
        scheduler_no_det = PatchScheduler(repo_path=self.repo_path)
        res = scheduler_no_det.analyze_schedule_impact(uuid.uuid4().hex, uuid.uuid4().hex)
        self.assertEqual(res, {"anomaly_detected": False, "impact_score": 0.5})

    def test_batch_schedule_patches_with_detector(self):
        batch_id = uuid.uuid4().hex
        patches_batch = [{"id": uuid.uuid4().hex}]
        expected = {"batch_id": batch_id, "approved": False}
        self.anomaly_detector.batch_analyze_patches.return_value = expected

        res = self.scheduler.batch_schedule_patches(batch_id, patches_batch)
        self.assertEqual(res, expected)

    def test_batch_schedule_patches_without_detector(self):
        scheduler_no_det = PatchScheduler(repo_path=self.repo_path)
        batch_id = uuid.uuid4().hex
        res = scheduler_no_det.batch_schedule_patches(batch_id, [])
        self.assertEqual(res, {"batch_id": batch_id, "approved": True})

    def test_schedule_patch(self):
        patch_id = uuid.uuid4().hex
        patch_data = {"patch_id": patch_id}
        digest = {"digest_id": uuid.uuid4().hex}
        res = self.scheduler.schedule_patch(patch_data, digest)
        self.assertEqual(res, {"status": "scheduled", "patch_id": patch_id})