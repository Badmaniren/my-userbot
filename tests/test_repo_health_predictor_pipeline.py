import unittest
from unittest.mock import patch, mock_open
import io
import json
import uuid
import random
import string
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline


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

    def test_analyze_health_valid_data(self):
        random_key = uuid.uuid4().hex
        random_value = "".join(random.choices(string.ascii_letters, k=10))
        raw_data = {random_key: random_value}

        result = self.pipeline.analyze_health(raw_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)
        self.assertTrue(0.0 <= result["score"] <= 1.0)

    def test_analyze_health_empty_data(self):
        with self.assertRaises(ValueError) as ctx:
            self.pipeline.analyze_health({})
        self.assertEqual(str(ctx.exception), "Empty raw data")

    def test_run_pipeline_with_content(self):
        random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        mock_stream = io.BytesIO(random_payload)

        is_success = self.pipeline.run_pipeline(mock_stream)
        self.assertTrue(is_success)

    def test_run_pipeline_empty_content(self):
        mock_stream = io.BytesIO(b"")

        is_success = self.pipeline.run_pipeline(mock_stream)
        self.assertFalse(is_success)

    def test_functional_pipeline_success(self):
        random_repo_id = uuid.uuid4().hex
        raw_data = {"repository_id": random_repo_id, "metrics": random.randint(100, 999)}

        mock_file_handle = mock_open()
        
        with patch("skills.repo_health_predictor_pipeline.os.makedirs") as mock_makedirs, \
             patch("skills.repo_health_predictor_pipeline.open", mock_file_handle) as mock_file, \
             patch("skills.repo_health_predictor_pipeline.json.dump") as mock_json_dump:

            result = repo_health_predictor_pipeline(raw_data)

            mock_makedirs.assert_called_once_with("reports", exist_ok=True)
            expected_path = f"reports/health_prediction_{random_repo_id}.json"
            mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
            
            mock_json_dump.assert_called_once()
            dumped_args = mock_json_dump.call_args[0]
            dumped_data = dumped_args[0]
            
            self.assertEqual(dumped_data["repository_id"], random_repo_id)
            self.assertEqual(dumped_data["status"], "success")
            self.assertIn("prediction_score", dumped_data)
            self.assertEqual(result, dumped_data)

    def test_functional_pipeline_empty_data(self):
        with self.assertRaises(ValueError) as ctx:
            repo_health_predictor_pipeline({})
        self.assertEqual(str(ctx.exception), "Empty raw data")


if __name__ == "__main__":
    unittest.main()