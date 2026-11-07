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
                "commits_count": random.randint(10, 500),
                "open_issues": random.randint(0, 50),
                "pull_requests_merged": random.randint(5, 100)
            }
        }
        self.report_path = f"reports/health_prediction_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_path):
            try:
                os.remove(self.report_path)
            except OSError:
                pass

    def test_repo_health_predictor_pipeline_functional(self):
        result = repo_health_predictor_pipeline(self.raw_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("repository_id"), self.repo_id)
        self.assertIn("prediction_score", result)
        
        score = result.get("prediction_score")
        self.assertIsInstance(score, float)
        self.assertTrue(0.0 <= score <= 1.0)

        self.assertTrue(os.path.exists(self.report_path))
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)
            
        self.assertEqual(file_content.get("repository_id"), self.repo_id)
        self.assertEqual(file_content.get("prediction_score"), score)
        self.assertEqual(file_content.get("status"), "success")

    def t_repo_health_predictor_pipeline_class_methods(self):
        pipeline = RepoHealthPredictorPipeline(endpoint="http://localhost", threshold=random.random())
        
        analysis_result = pipeline.analyze_health(self.raw_data)
        self.assertEqual(analysis_result.get("status"), "predicted")
        self.assertIn("score", analysis_result)
        
        class MockStream:
            def __init__(self, data):
                self.data = data
            def read(self):
                return self.data
                
        stream = MockStream(b"stream_content_test")
        self.assertTrue(pipeline.run_pipeline(stream))
        
        empty_stream = MockStream(b"")
        self.assertFalse(pipeline.run_pipeline(empty_stream))

    def test_empty_raw_data_raises_value_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        pipeline = RepoHealthPredictorPipeline()
        with self.assertRaises(ValueError):
            pipeline.analyze_health({})

if __name__ == "__main__":
    unittest.main()