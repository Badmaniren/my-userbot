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
                "commits_count": uuid.uuid4().int % 100,
                "open_issues": uuid.uuid4().int % 20
            }
        }
        self.report_path = f"reports/health_prediction_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_path):
            os.remove(self.report_path)

    def test_repo_health_predictor_pipeline_execution(self):
        result = repo_health_predictor_pipeline(self.raw_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repository_id"), self.repo_id)
        self.assertEqual(result.get("status"), "success")
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)

        self.assertTrue(os.path.exists(self.report_path), "Файл отчета не был создан на диске.")
        
        with open(self.report_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)
            
        self.assertEqual(saved_data.get("repository_id"), self.repo_id)
        self.assertEqual(saved_data.get("prediction_score"), result["prediction_score"])

    def p_test_class_pipeline_methods(self):
        pipeline = RepoHealthPredictorPipeline(endpoint="http://localhost", threshold=0.7)
        
        analysis_result = pipeline.analyze_health(self.raw_data)
        self.assertEqual(analysis_result.get("status"), "predicted")
        self.assertIn("score", analysis_result)

        class DummyStream:
            def __init__(self, content):
                self.content = content
            def read(self):
                return self.content

        stream_valid = DummyStream(b"some_data")
        self.assertTrue(pipeline.run_pipeline(stream_valid))

        stream_empty = DummyStream(b"")
        self.assertFalse(pipeline.run_pipeline(stream_empty))

if __name__ == "__main__":
    unittest.main()