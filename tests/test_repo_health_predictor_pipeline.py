import os
import json
import uuid
import random
import io
import unittest
from unittest.mock import patch, mock_open
from typing import Any, Dict

from skills.repo_health_predictor_pipeline import (
    RepoHealthPredictorPipeline,
    repo_health_predictor_pipeline
)


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def setUp(self):
        self.endpoint = f"https://{uuid.uuid4().hex}.api/v1"
        self.threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = RepoHealthPredictorPipeline(endpoint=self.endpoint, threshold=self.threshold)

    def test_init_properties(self):
        self.assertEqual(self.pipeline.endpoint, self.endpoint)
        self.assertEqual(self.pipeline.threshold, self.threshold)

    def test_analyze_health_empty_data(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze_health({})

    def test_analyze_health_valid_data(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        raw_data = {random_key: random_val}
        
        result = self.pipeline.analyze_health(raw_data)
        
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)
        self.assertTrue(0.0 <= result["score"] <= 1.0)

    def test_run_pipeline_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        res = self.pipeline.run_pipeline(empty_stream)
        self.assertFalse(res)

    def test_run_pipeline_valid_stream(self):
        random_payload = uuid.uuid4().bytes
        stream = io.BytesIO(random_payload)
        res = self.pipeline.run_pipeline(stream)
        self.assertTrue(res)

    def test_repo_health_predictor_pipeline_empty_data(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

    def test_repo_health_predictor_pipeline_success(self):
        repo_id = uuid.uuid4().hex
        raw_data = {"repository_id": repo_id, uuid.uuid4().hex: uuid.uuid4().hex}

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file, \
             patch("json.dump") as mock_json_dump:

            result = repo_health_predictor_pipeline(raw_data)

            mock_makedirs.assert_called_once_with("reports", exist_ok=True)
            expected_path = f"reports/health_prediction_{repo_id}.json"
            mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
            
            self.assertEqual(result["status"], "success")
            self.assertEqual(result["repository_id"], repo_id)
            self.assertIn("prediction_score", result)
            self.assertIsInstance(result["prediction_score"], float)
            self.assertTrue(0.0 <= result["prediction_score"] <= 1.0)
            
            mock_json_dump.assert_called_once()
            dumped_arg = mock_json_dump.call_args[0][0]
            self.assertEqual(dumped_arg["repository_id"], repo_id)


if __name__ == "__main__":
    unittest.main()