import unittest
from unittest.mock import patch, mock_open
import io
import os
import json
import uuid
import random
import requests
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_endpoint = f"https://{uuid.uuid4().hex}.com/api/v{random.randint(1,9)}"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = RepoHealthPredictorPipeline(endpoint=self.rand_endpoint, threshold=self.rand_threshold)

    def test_init_properties(self):
        self.assertEqual(self.pipeline.endpoint, self.rand_endpoint)
        self.assertEqual(self.pipeline.threshold, self.rand_threshold)

    def test_analyze_health_valid(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        raw_data = {rand_key: rand_val}
        
        result = self.pipeline.analyze_health(raw_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)

    def test_analyze_health_empty(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze_health({})

    def test_run_pipeline_with_content(self):
        rand_payload = uuid.uuid4().bytes
        stream = io.BytesIO(rand_payload)
        res = self.pipeline.run_pipeline(stream)
        self.assertTrue(res)

    def test_run_pipeline_empty(self):
        stream = io.BytesIO(b"")
        res = self.pipeline.run_pipeline(stream)
        self.assertFalse(res)

    def test_functional_pipeline_success(self):
        rand_repo_id = uuid.uuid4().hex
        raw_data = {"repository_id": rand_repo_id, "metrics": random.randint(100, 500)}

        with patch("os.makedirs") as mock_mkdirs, \
             patch("builtins.open", mock_open()) as mock_file:
            
            result = repo_health_predictor_pipeline(raw_data)
            
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["repository_id"], rand_repo_id)
            self.assertIn("prediction_score", result)
            self.assertIsInstance(result["prediction_score"], float)
            
            mock_mkdirs.assert_called_once_with("reports", exist_ok=True)
            mock_file.assert_called_once_with(f"reports/health_prediction_{rand_repo_id}.json", "w", encoding="utf-8")

    def test_functional_pipeline_empty(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

    def test_pipeline_external_call_mocking(self):
        rand_metric_id = uuid.uuid4().hex
        with patch("requests.post") as mock_post:
            mock_post.return_value.status_code = 200
            mock_post.return_value.json.return_value = {"status": "ok", "id": rand_metric_id}

            response = requests.post(self.pipeline.endpoint, json={"id": rand_metric_id})
            
            mock_post.assert_called_once_with(self.pipeline.endpoint, json={"id": rand_metric_id})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["id"], rand_metric_id)


if __name__ == "__main__":
    unittest.main()