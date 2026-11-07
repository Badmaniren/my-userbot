import unittest
import os
import json
import uuid
import random
from skills.repo_health_predictor_pipeline import repo_health_predictor_pipeline, RepoHealthPredictorPipeline

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.raw_data = {
            "repository_id": self.repo_id,
            "metrics": {
                "activity": random.randint(10, 100),
                "issues": random.randint(0, 10)
            }
        }
        self.reports_dir = "reports"

    def tearDown(self):
        report_path = os.path.join(self.reports_dir, f"health_prediction_{self.repo_id}.json")
        if os.path.exists(report_path):
            os.remove(report_path)

    def test_repo_health_predictor_pipeline_integration(self):
        result = repo_health_predictor_pipeline(self.raw_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["repository_id"], self.repo_id)
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)

        report_path = os.path.join(self.reports_dir, f"health_prediction_{self.repo_id}.json")
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["repository_id"], self.repo_id)
        self.assertEqual(saved_data["prediction_score"], result["prediction_score"])

    def class_interface_test(self):
        pipeline = RepoHealthPredictorPipeline(threshold=random.random())
        analysis = pipeline.analyze_health(self.raw_data)
        self.assertEqual(analysis["status"], "predicted")
        self.assertIn("score", analysis)

if __name__ == "__main__":
    unittest.main()