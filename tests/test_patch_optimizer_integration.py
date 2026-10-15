import unittest
import uuid
import random
import tempfile
import shutil
from pathlib import Path

from skills.patch_optimizer import PatchOptimizer, PatchOptimizerError
from skills.git_inspector import GitInspector
from skills.lesson_parser import LessonParser
from skills.patch_executor import PatchExecutor
from skills.patch_verifier import PatchVerifier
from skills.anomaly_detector import AnomalyDetector
from skills.system_telemetry import SystemTelemetry

class TestPatchOptimizerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.repo_path = self.test_dir

        self.git_inspector = GitInspector(self.repo_path)
        self.lesson_parser = LessonParser(self.git_inspector)
        self.patch_executor = PatchExecutor(self.repo_path, self.git_inspector, self.lesson_parser)
        self.patch_verifier = PatchVerifier(self.repo_path, self.git_inspector, self.patch_executor)

        self.anomaly_detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=random.uniform(0.5, 2.0),
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier
        )

        self.system_telemetry = SystemTelemetry(
            repo_path=self.repo_path,
            anomaly_detector=self.anomaly_detector,
            autonomous_engine=None
        )

        self.optimizer = PatchOptimizer(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector,
            patch_verifier=self.patch_verifier,
            anomaly_detector=self.anomaly_detector,
            system_telemetry=self.system_telemetry
        )

    def tearDown(self):
        shutil.rmtree(self.test_dir)

    def test_patch_optimization_and_prioritization(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(10.0, 100.0)
        self.system_telemetry.record_metric(metric_name, metric_value)

        patch_id = f"patch_{uuid.uuid4().hex[:8]}"
        target_file = f"src_{uuid.uuid4().hex[:6]}.py"

        file_path = Path(self.repo_path) / target_file
        file_path.write_text("print('initial')\n")

        patch_data = {
            "patch_id": patch_id,
            "file_path": target_file,
            "diff": f"--- {target_file}\n+++ {target_file}\n@@ -1,1 +1,1 @@\n-print('initial')\n+print('{patch_id}')\n",
            "telemetry_context": {
                "metric_name": metric_name,
                "expected_value": metric_value
            }
        }

        prioritized = self.optimizer.prioritize_patches([patch_data])
        self.assertIsInstance(prioritized, list)
        self.assertTrue(len(prioritized) > 0)
        self.assertEqual(prioritized[0]["patch_id"], patch_id)

        optimization_result = self.optimizer.optimize_and_apply(patch_data)
        self.assertIsInstance(optimization_result, dict)
        self.assertIn("success", optimization_result)
        self.assertTrue(optimization_result["success"])

        file_content = file_path.read_text()
        self.assertIn(patch_id, file_content)

if __name__ == "__main__":
    unittest.main()