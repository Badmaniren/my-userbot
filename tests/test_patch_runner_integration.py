import unittest
import uuid
import random
import tempfile
import os
from skills.patch_runner import patch_runner_pipeline
from skills.anomaly_logger import AnomalyLogger
from skills.git_inspector import GitInspector

class TestPatchRunnerIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.log_path = os.path.join(self.repo_path, f"anomaly_{uuid.uuid4()}.log")
        self.logger = AnomalyLogger(self.log_path)
        self.inspector = GitInspector(self.repo_path)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_patch_runner_full_pipeline_integration(self):
        random_id = str(uuid.uuid4())
        metric_name = f"metric_{random.randint(1000, 9999)}"
        metric_value = random.uniform(10.0, 100.0)

        self.logger.log_anomaly(
            source=f"test_source_{random_id}",
            severity="HIGH",
            details=f"Integration test anomaly payload {random_id}",
            telemetry_snapshot={"id": random_id, metric_name: metric_value}
        )

        anomalies = self.logger.get_anomalies()
        self.assertTrue(len(anomalies) > 0, "Логгер должен содержать хотя бы одну аномалию")

        pipeline_result = patch_runner_pipeline(
            repo_path=self.repo_path,
            log_path=self.log_path,
            target_id=random_id
        )

        self.assertIsNotNone(pipeline_result, "Пайплайн patch_runner не должен возвращать None")

        commit_history = self.inspector.get_commit_history(max_count=5)
        self.assertIsInstance(commit_history, list, "История коммитов должна быть списком")

if __name__ == "__main__":
    unittest.main()