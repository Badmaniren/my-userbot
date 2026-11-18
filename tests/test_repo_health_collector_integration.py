import unittest
import os
import tempfile
import uuid
import random
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError
from skills.repo_logger import RepoLogger

class TestRepoHealthCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.collector = RepoHealthCollector()
        self.logger = RepoLogger()

    def tearDown(self):
        self.test_dir.cleanup()

    def test_collect_metrics_integration_flow(self):
        session_id = str(uuid.uuid4())
        random_threshold = random.randint(10, 100)
        random_log_content = f"integration_test_metric_{uuid.uuid4()}"
        
        log_filename = f"session_{session_id}.log"
        log_file_path = os.path.join(self.repo_path, log_filename)
        
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(random_log_content)

        result = self.collector.collect_metrics(
            repo_path=self.repo_path,
            session_id=session_id,
            expected_threshold=random_threshold
        )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["threshold"], random_threshold)
        self.assertIn("log_content", result["metrics"])
        self.assertEqual(result["metrics"]["log_content"], random_log_content)

        report_filename = f"report_{session_id}.json"
        report_file_path = os.path.join(self.repo_path, report_filename)
        self.assertTrue(os.path.exists(report_file_path), "Отчет должен быть записан на диск.")

        with open(report_file_path, "r", encoding="utf-8") as f:
            report_data = json.load(f)
            
        self.assertEqual(report_data["session_id"], session_id)
        self.assertEqual(report_data["threshold"], random_threshold)
        self.assertEqual(report_data["metrics"]["log_content"], random_log_content)

    def test_collect_metrics_invalid_path(self):
        invalid_path = os.path.join(self.repo_path, str(uuid.uuid4()))
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=invalid_path)

if __name__ == "__main__":
    unittest.main()