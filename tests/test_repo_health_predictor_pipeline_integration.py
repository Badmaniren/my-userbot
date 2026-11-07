import unittest
import os
import json
import uuid
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.raw_data = {
            "repository_id": self.repo_id,
            "metrics": {
                "commits_per_week": uuid.uuid4().int % 100,
                "open_issues": uuid.uuid4().int % 50
            }
        }
        self.pipeline_instance = RepoHealthPredictorPipeline(endpoint="http://localhost/api", threshold=0.7)

    def tearDown(self):
        report_path = f"reports/health_prediction_{self.repo_id}.json"
        if os.path.exists(report_path):
            os.remove(report_path)

    def test_repo_health_predictor_functional_and_file_generation(self):
        result = repo_health_predictor_pipeline(self.raw_data)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["repository_id"], self.repo_id)
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)

        report_path = f"reports/health_prediction_{self.repo_id}.json"
        self.assertTrue(os.path.exists(report_path), "Integration error: report file was not created on disk.")

        with open(report_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data["repository_id"], self.repo_id)
        self.assertEqual(file_data["prediction_score"], result["prediction_score"])

    def test_class_based_pipeline_methods(self):
        analysis_res = self.pipeline_instance.analyze_health(self.raw_data)
        self.assertEqual(analysis_res["status"], "predicted")
        self.assertIn("score", analysis_res)

        from io import StringIO
        stream = StringIO("some historical metrics stream content")
        stream_res = self.pipeline_instance.run_pipeline(stream)
        self.assertTrue(stream_res)

    def test_empty_data_raises_value_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        with self.assertRaises(ValueError):
            self.pipeline_instance.analyze_health({})

if __name__ == "__main__":
    unittest.main()