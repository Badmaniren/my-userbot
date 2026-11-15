import unittest
import os
import json
import uuid
import random
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline
from io import StringIO

class TestRepoHealthPredictorPipelineIntegration(unittest.TestCase):
    
    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.raw_data = {
            "repository_id": self.repo_id,
            "metrics": {
                "commits_count": random.randint(10, 500),
                "open_issues": random.randint(0, 50),
                "pull_requests_merged": random.randint(5, 200)
            }
        }
        self.report_path = f"reports/health_prediction_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_path):
            try:
                os.remove(self.report_path)
            except OSError:
                pass

    def test_pipeline_class_execution(self):
        pipeline = RepoHealthPredictorPipeline(endpoint="http://localhost:8000", threshold=0.7)
        analysis_result = pipeline.analyze_health(self.raw_data)
        
        self.assertIsInstance(analysis_result, dict)
        self.assertEqual(analysis_result.get("status"), "predicted")
        self.assertIn("score", analysis_result)
        self.assertIsInstance(analysis_result["score"], float)

        stream_content = json.dumps(self.raw_data)
        stream = StringIO(stream_content)
        run_result = pipeline.run_pipeline(stream)
        self.assertTrue(run_result)

    def test_pipeline_function_integration_and_file_generation(self):
        result = repo_health_predictor_pipeline(self.raw_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("repository_id"), self.repo_id)
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)
        
        self.assertTrue(os.path.exists(self.report_path), "Report file was not created by the pipeline")
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data.get("repository_id"), self.repo_id)
        self.assertEqual(saved_data.get("prediction_score"), result["prediction_score"])
        self.assertEqual(saved_data.get("status"), "success")

    def test_pipeline_empty_data_raises_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        pipeline = RepoHealthPredictorPipeline()
        with self.assertRaises(ValueError):
            pipeline.analyze_health({})

if __name__ == "__main__":
    unittest.main()