import unittest
import os
import tempfile
import uuid
import random
import json

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.collector = RepoHealthCollector()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_collect_metrics_integration_flow(self):
        repo_path = self.test_dir.name
        session_id = str(uuid.uuid4())
        random_threshold = random.randint(10, 100)
        random_log_content = f"integration_test_log_message_{uuid.uuid4()}"

        log_filename = f"session_{session_id}.log"
        log_filepath = os.path.join(repo_path, log_filename)
        
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(random_log_content)

        report = self.collector.collect_metrics(
            repo_path=repo_path,
            session_id=session_id,
            expected_threshold=random_threshold
        )

        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["session_id"], session_id)
        self.assertEqual(report["repo_path"], repo_path)
        self.assertEqual(report["threshold"], random_threshold)
        self.assertIn("log_content", report["metrics"])
        self.assertEqual(report["metrics"]["log_content"], random_log_content)

        expected_report_filename = f"report_{session_id}.json"
        expected_report_filepath = os.path.join(repo_path, expected_report_filename)
        self.assertTrue(os.path.exists(expected_report_filepath))

        with open(expected_report_filepath, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["session_id"], session_id)
        self.assertEqual(saved_data["threshold"], random_threshold)
        self.assertEqual(saved_data["metrics"]["log_content"], random_log_content)

    def test_collect_metrics_invalid_path(self):
        invalid_path = os.path.join(self.test_dir.name, str(uuid.uuid4()))
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=invalid_path)

if __name__ == "__main__":
    unittest.main()