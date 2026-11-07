import unittest
import os
import json
import uuid
from skills.repo_health_predictor_pipeline import repo_health_predictor_pipeline, RepoHealthPredictorPipeline

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.raw_data = {
            "repository_id": self.repo_id,
            "metrics": {
                "commits_frequency": uuid.uuid4().hex,
                "open_issues": 42
            }
        }
        self.report_path = f"reports/health_prediction_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_path):
            try:
                os.remove(self.report_path)
            except OSError:
                pass

    def test_repo_health_predictor_pipeline_integration(self):
        result = repo_health_predictor_pipeline(self.raw_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("repository_id"), self.repo_id)
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)

        self.assertTrue(os.path.exists(self.report_path), "Report file was not created on disk")

        with open(self.report_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data.get("repository_id"), self.repo_id)
        self.assertEqual(saved_data.get("prediction_score"), result["prediction_score"])

    def test_class_pipeline_integration(self):
        pipeline = RepoHealthPredictorPipeline(endpoint="http://localhost", threshold=0.7)
        analysis = pipeline.analyze_health(self.raw_data)
        
        self.assertEqual(analysis.get("status"), "predicted")
        self.assertIn("score", analysis)
        self.assertIsInstance(analysis["score"], float)

if __name__ == "__main__":
    unittest.main()