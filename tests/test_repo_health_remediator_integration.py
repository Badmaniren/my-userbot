import unittest
import uuid
import random
import os
import tempfile
from skills.repo_health_remediator import RepoHealthRemediator
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline
from skills.repo_health_collector import RepoHealthCollector
from skills.repo_logger import RepoLogger

class TestRepoHealthRemediatorIntegration(unittest.TestCase):
    def setUp(self):
        self.test_dir = tempfile.mkdtemp()
        self.logger = RepoLogger()
        self.collector = RepoHealthCollector()
        self.predictor = RepoHealthPredictorPipeline()
        self.remediator = RepoHealthRemediator()
        
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_threshold = round(random.uniform(0.1, 0.9), 2)
        self.target_file = os.path.join(self.test_dir, f"health_report_{uuid.uuid4().hex[:6]}.json")

    def tearDown(self):
        if os.path.exists(self.target_file):
            os.remove(self.target_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_remediation_pipeline_integration(self):
        repo_data = {
            "path": self.test_dir,
            "metric": self.random_metric_name,
            "value": self.random_threshold
        }
        
        collected_metrics = self.collector.collect(repo_data)
        self.assertIsNotNone(collected_metrics)
        
        prediction = self.predictor.predict(collected_metrics)
        self.assertIsInstance(prediction, dict)
        
        remediation_payload = {
            "prediction_id": str(uuid.uuid4()),
            "repo_path": self.test_dir,
            "prediction_data": prediction,
            "target_output": self.target_file
        }
        
        result = self.remediator.apply_remediation(remediation_payload)
        
        self.assertIn("status", result)
        self.assertEqual(result["status"], "success")
        self.assertTrue(os.path.exists(self.target_file), "Интеграционный тест не создал целевой файл корректирующих мер")
        
        log_entry = self.logger.get_latest_entry()
        self.assertIsNotNone(log_entry)

if __name__ == "__main__":
    unittest.main()