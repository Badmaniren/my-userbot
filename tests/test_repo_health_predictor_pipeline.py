import unittest
from unittest.mock import patch, mock_open
import io
import os
import json
import uuid
import random
from skills.repo_health_predictor_pipeline import (
    RepoHealthPredictorPipeline,
    repo_health_predictor_pipeline
)


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def test_pipeline_class_initialization_defaults(self):
        rand_endpoint = f"https://{uuid.uuid4().hex}.internal/api"
        rand_threshold = round(random.uniform(0.1, 0.9), 2)
        
        pipeline = RepoHealthPredictorPipeline(endpoint=rand_endpoint, threshold=rand_threshold)
        self.assertEqual(pipeline.endpoint, rand_endpoint)
        self.assertEqual(pipeline.threshold, rand_threshold)

        default_pipeline = RepoHealthPredictorPipeline()
        self.assertIsNone(default_pipeline.endpoint)
        self.assertEqual(default_pipeline.threshold, 0.5)

    def test_analyze_health_success(self):
        pipeline = RepoHealthPredictorPipeline()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        raw_data = {rand_key: rand_val}

        with patch('random.random', return_value=0.77):
            res = pipeline.analyze_health(raw_data)

        self.assertEqual(res.get("status"), "predicted")
        self.assertEqual(res.get("score"), 0.77)

    def test_analyze_health_empty_raises_value_error(self):
        pipeline = RepoHealthPredictorPipeline()
        with self.assertRaises(ValueError):
            pipeline.analyze_health({})

        with self.assertRaises(ValueError):
            pipeline.analyze_health(None)

    def test_run_pipeline_with_content(self):
        pipeline = RepoHealthPredictorPipeline()
        rand_payload = uuid.uuid4().bytes
        stream = io.BytesIO(rand_payload)

        is_success = pipeline.run_pipeline(stream)
        self.assertTrue(is_success)

    def test_run_pipeline_empty_stream(self):
        pipeline = RepoHealthPredictorPipeline()
        stream = io.BytesIO(b"")

        is_success = pipeline.run_pipeline(stream)
        self.assertFalse(is_success)

    def test_functional_repo_health_predictor_pipeline_success(self):
        rand_repo_id = uuid.uuid4().hex
        rand_meta_key = uuid.uuid4().hex
        rand_meta_val = uuid.uuid4().hex
        
        raw_data = {
            "repository_id": rand_repo_id,
            rand_meta_key: rand_meta_val
        }

        mock_file = mock_open()
        
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file), \
             patch("random.uniform", return_value=0.88):
            
            result = repo_health_predictor_pipeline(raw_data)

        mock_makedirs.assert_called_once_with("reports", exist_ok=True)
        
        expected_path = f"reports/health_prediction_{rand_repo_id}.json"
        mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("repository_id"), rand_repo_id)
        self.assertEqual(result.get("prediction_score"), 0.88)

        handle = mock_file()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_dump = json.loads(written_data)
        self.assertEqual(parsed_dump["repository_id"], rand_repo_id)
        self.assertEqual(parsed_dump["prediction_score"], 0.88)

    def test_functional_repo_health_predictor_pipeline_empty_raises(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline(None)


if __name__ == "__main__":
    unittest.main()