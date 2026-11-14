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

    def test_collect_metrics_integration(self):
        random_session_id = str(uuid.uuid4())
        random_threshold = random.randint(10, 100)
        random_log_content = f"integration_test_metric_log_{uuid.uuid4()}"
        
        log_filename = f"session_{random_session_id}.log"
        log_filepath = os.path.join(self.test_dir.name, log_filename)
        
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(random_log_content)

        report = self.collector.collect_metrics(
            repo_path=self.test_dir.name,
            session_id=random_session_id,
            expected_threshold=random_threshold
        )

        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["session_id"], random_session_id)
        self.assertEqual(report["repo_path"], self.test_dir.name)
        self.assertEqual(report["threshold"], random_threshold)
        self.assertIn("log_content", report["metrics"])
        self.assertEqual(report["metrics"]["log_content"], random_log_content)

        report_filename = f"report_{random_session_id}.json"
        report_filepath = os.path.join(self.test_dir.name, report_filename)
        self.assertTrue(os.path.exists(report_filepath))

        with open(report_filepath, "r", encoding="utf-8") as f:
            saved_report = json.load(f)

        self.assertEqual(saved_report["session_id"], random_session_id)
        self.assertEqual(saved_report["threshold"], random_threshold)
        self.assertEqual(saved_report["metrics"]["log_content"], random_log_content)

    def test_collect_metrics_non_existent_path(self):
        non_existent_path = os.path.join(self.test_dir.name, str(uuid.uuid4()))
        random_session_id = str(uuid.uuid4())

        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(
                repo_path=non_existent_path,
                session_id=random_session_id
            )

if __name__ == "__main__":
    unittest.main()