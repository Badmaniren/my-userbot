import unittest
import os
import json
import uuid
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.raw_data = {
            "repository_id": self.repo_id,
            "metrics": {
                "commits_count": int(uuid.uuid4().int % 1000),
                "open_issues": int(uuid.uuid4().int % 50)
            }
        }
        self.report_path = f"reports/health_prediction_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_path):
            try:
                os.remove(self.report_path)
            except OSError:
                pass

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

    def class_pipeline_methods_test(self):
        pipeline = RepoHealthPredictorPipeline(endpoint="http://localhost", threshold=0.7)
        
        analysis_result = pipeline.analyze_health(self.raw_data)
        self.assertEqual(analysis_result["status"], "predicted")
        self.assertIn("score", analysis_result)

        class MockStream:
            def __init__(self, data):
                self.data = data
            def read(self):
                return self.data

        valid_stream = MockStream(b"test_stream_content")
        self.assertTrue(pipeline.run_pipeline(valid_stream))

        empty_stream = MockStream(b"")
        self.assertFalse(pipeline.run_pipeline(empty_stream))

    def test_empty_data_raises_value_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        pipeline = RepoHealthPredictorPipeline()
        with self.assertRaises(ValueError):
            pipeline.analyze_health({})

if __name__ == "__main__":
    unittest.main()