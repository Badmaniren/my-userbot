import unittest
import uuid
import random
import os
import tempfile
from skills.repo_health_collector import RepoHealthCollector
from skills.repo_auditor import RepoAuditor
from skills.repo_logger import RepoLogger

class TestRepoHealthCollectorIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.collector = RepoHealthCollector()
        self.auditor = RepoAuditor()
        self.logger = RepoLogger()
        self.unique_repo_id = str(uuid.uuid4())
        self.random_metric_value = random.randint(100, 999)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_health_collection_pipeline_integration(self):
        dummy_file_name = f"health_metric_{self.unique_repo_id}.log"
        dummy_file_path = os.path.join(self.test_dir.name, dummy_file_name)
        
        log_content = f"REPO_ID: {self.unique_repo_id}, METRIC: {self.random_metric_value}"
        
        self.logger.log_event(dummy_file_path, log_content)
        
        audit_result = self.auditor.audit_repository(self.test_dir.name)
        self.assertIsNotNone(audit_result)

        health_report = self.collector.collect_metrics(
            repo_path=self.test_dir.name,
            session_id=self.unique_repo_id,
            expected_threshold=self.random_metric_value
        )

        self.assertIsInstance(health_report, dict)
        self.assertIn("status", health_report)
        self.assertEqual(health_report.get("session_id"), self.unique_repo_id)
        
        report_file_path = os.path.join(self.test_dir.name, f"report_{self.unique_repo_id}.json")
        self.assertTrue(os.path.exists(dummy_file_path), "Исходный лог-файл должен существовать.")

if __name__ == "__main__":
    unittest.main()