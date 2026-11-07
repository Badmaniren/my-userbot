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
                "commit_frequency": round(uuid.uuid4().int % 100 / 10.0, 2),
                "open_issues": uuid.uuid4().int % 50
            }
        }
        self.report_path = f"reports/health_prediction_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_path):
            os.remove(self.report_path)

    def test_pipeline_execution_and_persistence(self):
        result = repo_health_predictor_pipeline(self.raw_data)
        
        self.assertEqual(result["status"], "success")
        self.assertEqual(result["repository_id"], self.repo_id)
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)

        self.assertTrue(os.path.exists(self.report_path))
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data["repository_id"], self.repo_id)
        self.assertEqual(saved_data["prediction_score"], result["prediction_score"])

    def test_pipeline_class_methods(self):
        pipeline = RepoHealthPredictorPipeline(threshold=0.7)
        
        analysis = pipeline.analyze_health(self.raw_data)
        self.assertEqual(analysis["status"], "predicted")
        self.assertIsInstance(analysis["score"], float)

        from io import StringIO
        stream = StringIO("non-empty stream content")
        stream_result = pipeline.run_pipeline(stream)
        self.assertTrue(stream_result)

    def test_empty_data_raises_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        pipeline = RepoHealthPredictorPipeline()
        with self.assertRaises(ValueError):
            pipeline.analyze_health({})


if __name__ == "__main__":
    unittest.main()