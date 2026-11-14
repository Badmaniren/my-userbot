import unittest
from unittest.mock import patch, mock_open
import io
import uuid
import random
import string
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def setUp(self):
        self.random_endpoint = f"https://{uuid.uuid4().hex}.internal/api/v{random.randint(1, 9)}"
        self.random_threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = RepoHealthPredictorPipeline(
            endpoint=self.random_endpoint,
            threshold=self.random_threshold
        )

    def test_init_state(self):
        self.assertEqual(self.pipeline.endpoint, self.random_endpoint)
        self.assertEqual(self.pipeline.threshold, self.random_threshold)

    def test_analyze_health_empty_data(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze_health({})

    def test_analyze_health_valid_data(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        raw_data = {rand_key: rand_val}

        result = self.pipeline.analyze_health(raw_data)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)

    def test_run_pipeline_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        res = self.pipeline.run_pipeline(empty_stream)
        self.assertFalse(res)

    def test_run_pipeline_valid_stream(self):
        random_payload = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode("utf-8")
        stream = io.BytesIO(random_payload)
        res = self.pipeline.run_pipeline(stream)
        self.assertTrue(res)

    def test_functional_predictor_empty_data(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})

    def test_functional_predictor_creates_report_file(self):
        repo_id = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(100, 999)
        raw_data = {
            "repository_id": repo_id,
            metric_key: metric_val
        }

        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_open()) as mock_file:
            
            result = repo_health_predictor_pipeline(raw_data)

            mock_makedirs.assert_called_once_with("reports", exist_ok=True)
            mock_file.assert_called_once_with(f"reports/health_prediction_{repo_id}.json", "w", encoding="utf-8")
            
            self.assertEqual(result["repository_id"], repo_id)
            self.assertEqual(result["status"], "success")
            self.assertIn("prediction_score", result)


if __name__ == "__main__":
    unittest.main()