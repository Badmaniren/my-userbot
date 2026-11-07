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
        self.endpoint_url = f"https://{uuid.uuid4().hex}.api/v1/predict"
        self.threshold_val = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = RepoHealthPredictorPipeline(
            endpoint=self.endpoint_url,
            threshold=self.threshold_val
        )

    def test_init_properties(self):
        self.assertEqual(self.pipeline.endpoint, self.endpoint_url)
        self.assertEqual(self.pipeline.threshold, self.threshold_val)

        default_pipeline = RepoHealthPredictorPipeline()
        self.assertIsNone(default_pipeline.endpoint)
        self.assertEqual(default_pipeline.threshold, 0.5)

    def test_analyze_health_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        raw_data = {rand_key: rand_val}

        with patch("random.uniform", return_value=0.77):
            result = self.pipeline.analyze_health(raw_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("status"), "predicted")
        self.assertEqual(result.get("score"), 0.77)

    def test_analyze_health_empty_raises(self):
        with self.assertRaises(ValueError) as ctx:
            self.pipeline.analyze_health({})
        self.assertEqual(str(ctx.exception), "Empty raw data")

    def test_run_pipeline_with_content(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode("utf-8")
        stream_mock = io.BytesIO(random_bytes)

        res = self.pipeline.run_pipeline(stream_mock)
        self.assertTrue(res)

    def test_run_pipeline_empty_stream(self):
        stream_mock = io.BytesIO(b"")

        res = self.pipeline.run_pipeline(stream_mock)
        self.assertFalse(res)

    def test_functional_repo_health_predictor_pipeline(self):
        repo_id = uuid.uuid4().hex
        raw_data = {"repository_id": repo_id, uuid.uuid4().hex: random.randint(1, 100)}
        expected_score = round(random.uniform(0.0, 1.0), 4)

        mock_file_handle = mock_open()
        
        with patch("random.uniform", return_value=expected_score), \
             patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file_handle):

            result = repo_health_predictor_pipeline(raw_data)

        self.assertEqual(result.get("status"), "success")
        self.assertEqual(result.get("repository_id"), repo_id)
        self.assertEqual(result.get("prediction_score"), expected_score)

        mock_makedirs.assert_called_once_with("reports", exist_ok=True)
        mock_file_handle.assert_called_once_with(
            f"reports/health_prediction_{repo_id}.json",
            "w",
            encoding="utf-8"
        )

        handle = mock_file_handle()
        written_data = "".join(call.args[0] for call in handle.write.mock_calls)
        parsed_json = json.loads(written_data)

        self.assertEqual(parsed_json.get("repository_id"), repo_id)
        self.assertEqual(parsed_json.get("prediction_score"), expected_score)

    def test_functional_repo_health_predictor_pipeline_empty_raises(self):
        with self.assertRaises(ValueError) as ctx:
            repo_health_predictor_pipeline({})
        self.assertEqual(str(ctx.exception), "Empty raw data")


if __name__ == "__main__":
    unittest.main()