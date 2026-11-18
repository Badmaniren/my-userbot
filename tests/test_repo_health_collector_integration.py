import unittest
import os
import uuid
import json
import tempfile
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.collector = RepoHealthCollector()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_collect_metrics_integration_flow(self):
        session_id = f"session_{uuid.uuid4().hex}"
        threshold = int(uuid.uuid4().int % 100)
        log_content = f"test_metric_data_{uuid.uuid4().hex}"
        
        log_filename = f"{session_id}_audit.log"
        log_file_path = os.path.join(self.repo_path, log_filename)
        
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(log_content)

        report = self.collector.collect_metrics(
            repo_path=self.repo_path,
            session_id=session_id,
            expected_threshold=threshold
        )

        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["session_id"], session_id)
        self.assertEqual(report["repo_path"], self.repo_path)
        self.assertEqual(report["threshold"], threshold)
        self.assertIn("log_content", report["metrics"])
        self.assertEqual(report["metrics"]["log_content"], log_content)

        expected_report_filename = f"report_{session_id}.json"
        expected_report_path = os.path.join(self.repo_path, expected_report_filename)
        
        self.assertTrue(os.path.exists(expected_report_path))

        with open(expected_report_path, "r", encoding="utf-8") as f:
            saved_report = json.load(f)

        self.assertEqual(saved_report["status"], "healthy")
        self.assertEqual(saved_report["session_id"], session_id)
        self.assertEqual(saved_report["threshold"], threshold)
        self.assertEqual(saved_report["metrics"]["log_content"], log_content)

    def test_collect_metrics_nonexistent_path(self):
        invalid_path = os.path.join(self.repo_path, str(uuid.uuid4()))
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=invalid_path)

if __name__ == "__main__":
    unittest.main()