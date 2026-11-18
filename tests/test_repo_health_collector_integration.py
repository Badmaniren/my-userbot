import unittest
import os
import tempfile
import uuid
import random
import json

from skills.repo_health_collector import RepoHealthCollector, RepoHealthError
from skills.repo_logger import RepoLogger

class TestRepoHealthCollectorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name
        self.session_id = str(uuid.uuid4())
        self.random_threshold = random.randint(10, 1000)
        self.random_content = f"log_data_{uuid.uuid4()}"
        
        self.log_filename = f"session_{self.session_id}.log"
        self.log_filepath = os.path.join(self.repo_path, self.log_filename)
        
        with open(self.log_filepath, "w", encoding="utf-8") as f:
            f.write(self.random_content)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_collect_metrics_integration(self):
        collector = RepoHealthCollector(repo_path=self.repo_path)
        
        self.assertIsInstance(collector.logger, RepoLogger)
        
        result = collector.collect_metrics(
            repo_path=self.repo_path,
            session_id=self.session_id,
            expected_threshold=self.random_threshold
        )
        
        self.assertEqual(result["status"], "healthy")
        self.assertEqual(result["repo_path"], self.repo_path)
        self.assertEqual(result["session_id"], self.session_id)
        self.assertEqual(result["threshold"], self.random_threshold)
        self.assertIn("log_content", result["metrics"])
        self.assertEqual(result["metrics"]["log_content"], self.random_content)
        
        report_filename = os.path.join(self.repo_path, f"report_{self.session_id}.json")
        self.assertTrue(os.path.exists(report_filename))
        
        with open(report_filename, "r", encoding="utf-8") as f:
            saved_report = json.load(f)
            
        self.assertEqual(saved_report["session_id"], self.session_id)
        self.assertEqual(saved_report["threshold"], self.random_threshold)
        self.assertEqual(saved_report["metrics"]["log_content"], self.random_content)

    def test_collect_metrics_nonexistent_repo(self):
        bad_path = os.path.join(self.repo_path, str(uuid.uuid4()))
        collector = RepoHealthCollector()
        
        with self.assertRaises(RepoHealthError):
            collector.collect_metrics(repo_path=bad_path, session_id=self.session_id)

if __name__ == "__main__":
    unittest.main()