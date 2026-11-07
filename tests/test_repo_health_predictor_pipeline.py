import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
import string
from skills.repo_health_predictor_pipeline import (
    RepoHealthPredictorPipeline,
    repo_health_predictor_pipeline
)


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def setUp(self):
        self.random_endpoint = f"https://{uuid.uuid4().hex}.api/v1/health"
        self.random_threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = RepoHealthPredictorPipeline(
            endpoint=self.random_endpoint,
            threshold=self.random_threshold
        )

    def test_init_properties(self):
        self.assertEqual(self.pipeline.endpoint, self.random_endpoint)
        self.assertEqual(self.pipeline.threshold, self.random_threshold)

    def test_analyze_health_empty_data_raises_error(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze_health({})

    def test_analyze_health_valid_data(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        raw_data = {random_key: random_val}

        result = self.pipeline.analyze_health(raw_data)
        
        self.assertIn("status", result)
        self.assertEqual(result["status"], "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)
        self.assertTrue(0.0 <= result["score"] <= 1.0)

    def test_run_pipeline_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        res = self.pipeline.run_pipeline(empty_stream)
        self.assertFalse(res)

    def test_run_pipeline_valid_stream(self):
        random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode("utf-8")
        valid_stream = io.BytesIO(random_payload)
        res = self.pipeline.run_pipeline(valid_stream)
        self.assertTrue(res)

    def test_functional_pipeline_empty_data_raises_error(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

    def test_functional_pipeline_success(self):
        random_repo_id = f"repo-{uuid.uuid4().hex[:8]}"
        raw_data = {"repository_id": random_repo_id, "metrics": random.randint(100, 999)}

        mock_file_handle = mock_open()
        
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file_handle):
            
            result = repo_health_predictor_pipeline(raw_data)

            mock_makedirs.assert_called_once_with("reports", exist_ok=True)
            
            expected_path = f"reports/health_prediction_{random_repo_id}.json"
            mock_file_handle.assert_called_once_with(expected_path, "w", encoding="utf-8")

            self.assertEqual(result["status"], "success")
            self.assertEqual(result["repository_id"], random_repo_id)
            self.assertIn("prediction_score", result)
            self.assertIsInstance(result["prediction_score"], float)

            written_content = "".join(call.args[0] for call in mock_file_handle().write.mock_calls)
            parsed_json = json.loads(written_content)
            self.assertEqual(parsed_json["repository_id"], random_repo_id)
            self.assertEqual(parsed_json["status"], "success")
            self.assertEqual(parsed_json["prediction_score"], result["prediction_score"])


if __name__ == "__main__":
    unittest.main()