import unittest
import os
import json
import uuid
import random
from skills.repo_health_collector import RepoHealthCollector, RepoHealthError

class TestRepoHealthCollectorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.collector = RepoHealthCollector()
        self.test_repo_path = f"test_repo_{uuid.uuid4().hex}"
        os.makedirs(self.test_repo_path, exist_ok=True)
        
    def tearDown(self):
        if os.path.exists(self.test_repo_path):
            for filename in os.listdir(self.test_repo_path):
                file_path = os.path.join(self.test_repo_path, filename)
                try:
                    if os.path.isfile(file_path):
                        os.unlink(file_path)
                except Exception:
                    pass
            try:
                os.rmdir(self.test_repo_path)
            except Exception:
                pass

    def test_collect_metrics_integration_flow(self):
        session_id = uuid.uuid4().hex
        random_log_content = f"latency_benchmark_{random.randint(100, 999)}ms"
        expected_threshold = random.randint(50, 500)
        
        log_filename = f"session_{session_id}.log"
        log_file_path = os.path.join(self.test_repo_path, log_filename)
        
        with open(log_file_path, "w", encoding="utf-8") as f:
            f.write(random_log_content)
            
        report = self.collector.collect_metrics(
            repo_path=self.test_repo_path,
            session_id=session_id,
            expected_threshold=expected_threshold
        )
        
        self.assertEqual(report["status"], "healthy")
        self.assertEqual(report["session_id"], session_id)
        self.assertEqual(report["repo_path"], self.test_repo_path)
        self.assertEqual(report["threshold"], expected_threshold)
        self.assertIn("log_content", report["metrics"])
        self.assertEqual(report["metrics"]["log_content"], random_log_content)
        
        report_filename = f"report_{session_id}.json"
        report_file_path = os.path.join(self.test_repo_path, report_filename)
        self.assertTrue(os.path.exists(report_file_path), "Файл отчета должен быть создан на диске.")
        
        with open(report_file_path, "r", encoding="utf-8") as f:
            saved_report = json.load(f)
            
        self.assertEqual(saved_report["session_id"], session_id)
        self.assertEqual(saved_report["threshold"], expected_threshold)
        self.assertEqual(saved_report["metrics"]["log_content"], random_log_content)

    def test_collect_metrics_invalid_path(self):
        invalid_path = f"nonexistent_repo_{uuid.uuid4().hex}"
        session_id = uuid.uuid4().hex
        
        with self.assertRaises(RepoHealthError):
            self.collector.collect_metrics(repo_path=invalid_path, session_id=session_id)

if __name__ == "__main__":
    unittest.main()