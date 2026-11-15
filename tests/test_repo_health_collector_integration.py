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
        session_id = str(uuid.uuid4())
        random_threshold = random.randint(10, 100)
        random_log_content = f"Health check status OK. Metric value: {random.randint(1000, 9999)}"
        
        log_file_name = f"session_{session_id}.log"
        log_file_path = os.path.join(self.test_dir.name, log_file_name)
        
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(random_log_content)

        report = self.collector.collect_metrics(
            repo_path=self.test_dir.name,
            session_id=session_id,
            expected_threshold=random_threshold
        )

        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["session_id"], session_id)
        self.assertEqual(report["repo_path"], self.test_dir.name)
        self.assertEqual(report["threshold"], random_threshold)
        self.assertIn("log_content", report["metrics"])
        self.assertEqual(report["metrics"]["log_content"], random_log_content)

        expected_report_filename = f"report_{session_id}.json"
        expected_report_filepath = os.path.join(self.test_dir.name, expected_report_filename)
        self.assertTrue(os.path.exists(expected_report_filepath))

        with open(expected_report_filepath, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            self.assertEqual(saved_data["session_id"], session_id)
            self.assertEqual(saved_data["threshold"], random_threshold)
            self.assertEqual(saved_data["metrics"]["log_content"], random_log_content)

    def test_collect_metrics_invalid_path_raises_error(self):
        non_existent_path = os.path.join(self.test_dir.name, str(uuid.uuid4()))
        session_id = str(uuid.uuid4())

        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(
                repo_path=non_existent_path,
                session_id=session_id
            )

if __name__ == "__main__":
    unittest.main()