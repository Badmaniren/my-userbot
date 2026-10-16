import unittest
import uuid
import random
import tempfile
import os
import subprocess
from skills.anomaly_mapper import AnomalyMapper
from skills.anomaly_detector import AnomalyDetector
from skills.git_inspector import GitInspector

class TestAnomalyMapperIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        subprocess.run(["git", "init", self.repo_path], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.name", "Test User"], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "config", "user.email", "test@example.com"], check=True, capture_output=True)

        self.file_name = f"service_{uuid.uuid4().hex[:8]}.py"
        self.file_path = os.path.join(self.repo_path, self.file_name)

        random_val = random.randint(100, 500)
        with open(self.file_path, "w") as f:
            f.write(f"LATENCY = {random_val}\n")

        subprocess.run(["git", "-C", self.repo_path, "add", self.file_name], check=True, capture_output=True)
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", "Initial commit"], check=True, capture_output=True)

        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        self.git_inspector = GitInspector(repo_path=self.repo_path)
        self.anomaly_detector = AnomalyDetector(
            repo_path=self.repo_path,
            threshold=50.0,
            git_inspector=self.git_inspector,
            patch_verifier=None
        )

        self.anomaly_mapper = AnomalyMapper(
            anomaly_detector=self.anomaly_detector,
            git_inspector=self.git_inspector
        )

    def tearDown(self):
        self.test_dir.cleanup()

    def test_anomaly_mapper_integration_real_flow(self):
        new_latency = random.randint(1000, 5000)
        with open(self.file_path, "w") as f:
            f.write(f"LATENCY = {new_latency}\n")

        subprocess.run(["git", "-C", self.repo_path, "add", self.file_name], check=True, capture_output=True)
        commit_message = f"Update latency to {new_latency} {uuid.uuid4().hex[:4]}"
        subprocess.run(["git", "-C", self.repo_path, "commit", "-m", commit_message], check=True, capture_output=True)

        self.anomaly_detector.record_metric(self.metric_name, 100.0)
        self.anomaly_detector.record_metric(self.metric_name, float(new_latency))

        mapping_result = self.anomaly_mapper.map_anomaly_to_commit(
            metric_name=self.metric_name,
            target_value=float(new_latency)
        )

        self.assertIsInstance(mapping_result, dict)
        self.assertIn("commit_hash", mapping_result)
        self.assertIn("file_changes", mapping_result)

        changed_files = mapping_result["file_changes"]
        self.assertTrue(any(self.file_name in str(cf) for cf in changed_files))

if __name__ == "__main__":
    unittest.main()