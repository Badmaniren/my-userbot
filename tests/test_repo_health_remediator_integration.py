import unittest
import os
import json
import uuid
import random
from skills.repo_health_remediator import RepoHealthRemediator
from skills.repo_logger import RepoLogger

class TestRepoHealthRemediatorIntegration(unittest.TestCase):
    def setUp(self):
        self.remediator = RepoHealthRemediator()
        self.random_uuid = str(uuid.uuid4())
        self.repo_path = f"./test_repo_{self.random_uuid}"
        self.target_output = os.path.join(self.repo_path, "remediation_report.json")
        
        self.metric = f"metric_{random.randint(1, 100)}"
        self.predicted_value = round(random.uniform(0.6, 1.0), 2)
        self.threshold = 0.5
        self.recommended_action = "optimize"

    def tearDown(self):
        if os.path.exists(self.target_output):
            os.remove(self.target_output)
        if os.path.exists(self.repo_path):
            try:
                os.rmdir(self.repo_path)
            except OSError:
                pass

    def test_apply_remediation_integration_file_and_logger(self):
        prediction_data = {
            "target_output": self.target_output,
            "repo_path": self.repo_path,
            "prediction_id": self.random_uuid,
            "prediction_data": {
                "metric": self.metric,
                "predicted_value": self.predicted_value,
                "threshold": self.threshold,
                "recommended_action": self.recommended_action
            }
        }

        result = self.remediator.apply_remediation(prediction_data)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("repo_path"), self.repo_path)

        self.assertTrue(os.path.exists(self.target_output), "Интеграционный тест не создал целевой файл отчета.")

        with open(self.target_output, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data.get("repo_path"), self.repo_path)
        self.assertEqual(saved_data.get("metric"), self.metric)
        self.assertEqual(saved_data.get("recommended_action"), self.recommended_action)
        self.assertEqual(saved_data.get("status"), "success")

        logger = RepoLogger(repo_path=self.repo_path)
        self.assertIsInstance(logger, RepoLogger)

if __name__ == "__main__":
    unittest.main()