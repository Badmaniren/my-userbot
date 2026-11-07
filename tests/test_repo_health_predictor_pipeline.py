import unittest
from unittest.mock import patch, mock_open
import io
import os
import json
import uuid
import random
import string

from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def setUp(self):
        self.endpoint = f"https://{uuid.uuid4().hex}.com/api/v{random.randint(1,9)}"
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = RepoHealthPredictorPipeline(endpoint=self.endpoint, threshold=self.threshold)

    def test_init_sets_attributes(self):
        rand_endpoint = f"http://{uuid.uuid4().hex}.net"
        rand_threshold = round(random.uniform(0.0, 1.0), 2)
        instance = RepoHealthPredictorPipeline(endpoint=rand_endpoint, threshold=rand_threshold)
        self.assertEqual(instance.endpoint, rand_endpoint)
        self.assertEqual(instance.threshold, rand_threshold)

    def test_analyze_health_empty_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze_health({})

        with self.assertRaises(ValueError):
                self.pipeline.analyze_health(None)

    def test_analyze_health_returns_valid_structure(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        raw_data = {rand_key: rand_val}
        
        result = self.pipeline.analyze_health(raw_data)
        
        self.assertIn("status", result)
        self.assertEqual(result["status"], "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)
        self.assertTrue(0.0 <= result["score"] <= 1.0)

    def test_run_pipeline_empty_stream_returns_false(empty_self):
        pipeline = RepoHealthPredictorPipeline()
        empty_stream = io.BytesIO(b"")
        result = pipeline.run_pipeline(empty_stream)
        empty_self.assertFalse(result)

    def test_run_pipeline_valid_stream_returns_true(empty_self):
        pipeline = RepoHealthPredictorPipeline()
        random_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=random.randint(10, 50))).encode('utf-8')
        valid_stream = io.BytesIO(random_bytes)
        result = pipeline.run_pipeline(valid_stream)
        empty_self.assertTrue(result)

    def test_functional_pipeline_empty_data_raises_value_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline(None)

    @patch("skills.repo_health_predictor_pipeline.os.makedirs")
    @patch("builtins.open", new_callable=mock_open)
    @patch("skills.repo_health_predictor_pipeline.json.dump")
    def test_repo_health_predictor_pipeline_success(self, mock_json_dump, mock_file_open, mock_makedirs):
        repo_id = uuid.uuid4().hex
        raw_data = {
            "repository_id": repo_id,
            uuid.uuid4().hex: uuid.uuid4().hex
        }

        result = repo_health_predictor_pipeline(raw_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["repository_id"], repo_id)
        self.assertIn("prediction_score", result)
        self.assertIsInstance(result["prediction_score"], float)

        mock_makedirs.assert_called_once_with("reports", exist_ok=True)
        expected_path = f"reports/health_prediction_{repo_id}.json"
        mock_file_open.assert_called_once_with(expected_path, "w", encoding="utf-8")
        mock_json_dump.assert_called_once()
        
        dumped_args = mock_json_dump.call_args[0]
        self.assertEqual(dumped_args[0]["repository_id"], repo_id)
        self.assertEqual(dumped_args[0]["status"], "success")


if __name__ == "__main__":
    unittest.main()