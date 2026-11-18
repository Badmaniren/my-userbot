import os
import json
import uuid
import random
import unittest
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollectorIntegration(unittest.TestCase):
    def setUp(self):
        self.collector = RepoHealthCollector()
        self.test_dir = f"test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.test_dir, exist_ok=True)

    def tearDown(self):
        if os.path.exists(self.test_dir):
            for root, dirs, files in os.walk(self.test_dir, topdown=False):
                for name in files:
                    os.remove(os.path.join(root, name))
                for name in dirs:
                    os.rmdir(os.path.join(root, name))
            os.rmdir(self.test_dir)

    def test_collect_metrics_integration_success(self):
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        expected_threshold = random.randint(10, 100)
        log_filename = f"{session_id}_activity.log"
        log_filepath = os.path.join(self.test_dir, log_filename)
        
        random_content = f"Log entry data {uuid.uuid4().hex}"
        with open(log_filepath, "w", encoding="utf-8") as f:
            f.write(random_content)

        result = self.collector.collect_metrics(
            repo_path=self.test_dir,
            session_id=session_id,
            expected_threshold=expected_threshold
        )

        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.test_dir)
        self.assertEqual(result["session_id"], session_id)
        self.assertEqual(result["threshold"], expected_threshold)
        self.assertIn("log_content", result["metrics"])
        self.assertEqual(result["metrics"]["log_content"], random_content)

        report_filename = os.path.join(self.test_dir, f"report_{session_id}.json")
        self.assertTrue(os.path.exists(report_filename))

        with open(report_filename, "r", encoding="utf-8") as f:
            saved_report = json.load(f)

        self.assertEqual(saved_report["session_id"], session_id)
        self.assertEqual(saved_report["threshold"], expected_threshold)
        self.assertEqual(saved_report["metrics"]["log_content"], random_content)

    def test_collect_metrics_nonexistent_repo(self):
        bad_path = f"nonexistent_{uuid.uuid4().hex}"
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=bad_path, session_id=session_id)

if __name__ == "__main__":
    unittest.main()