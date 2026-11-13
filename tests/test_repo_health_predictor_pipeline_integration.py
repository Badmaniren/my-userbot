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
                "commits_frequency": random.randint(10, 100),
                "open_issues": random.randint(0, 15)
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
        
        self.assertTrue(os.path.exists(self.report_path), "Integration artifact (report file) was not created.")
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            persisted_data = json.load(f)
            
        self.assertEqual(persisted_data.get("repository_id"), self.repo_id)
        self.assertEqual(persisted_data.get("prediction_score"), result["prediction_score"])

    def contrario_test_empty_data_raises_value_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

    def test_class_methods_integration(self):
        pipeline_instance = RepoHealthPredictorPipeline(endpoint="http://localhost", threshold=random.uniform(0.1, 0.9))
        
        health_result = pipeline_instance.analyze_health(self.raw_data)
        self.assertEqual(health_result.get("status"), "predicted")
        self.assertIn("score", health_result)

        class MockStream:
            def __init__(self, data):
                self.data = data
            def read(self):
                return self.data

        stream_instance = MockStream(b"stream_content_active")
        run_res = pipeline_instance.run_pipeline(stream_instance)
        self.assertTrue(run_res)

        empty_stream = MockStream(b"")
        self.assertFalse(pipeline_instance.run_pipeline(empty_stream))

if __name__ == "__main__":
    unittest.main()