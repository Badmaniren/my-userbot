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
        self.random_endpoint = f"https://{uuid.uuid4().hex}.{random.choice(['com', 'org', 'net'])}/{uuid.uuid4().hex}"
        self.random_threshold = round(random.uniform(0.1, 0.9), 2)
        self.predictor = RepoHealthPredictorPipeline(endpoint=self.random_endpoint, threshold=self.random_threshold)

    def test_init_properties(self):
        self.assertEqual(self.predictor.endpoint, self.random_endpoint)
        self.assertEqual(self.predictor.threshold, self.random_threshold)

    def test_analyze_health_empty_data_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            self.predictor.analyze_health({})
        self.assertEqual(str(ctx.exception), "Empty raw data")

    def test_analyze_health_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        raw_data = {random_key: random_val}

        with patch('random.uniform', return_value=0.777):
            result = self.predictor.analyze_health(raw_data)

        self.assertEqual(result["status"], "predicted")
        self.assertAlmostEqual(result["score"], 0.777)

    def test_run_pipeline_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        is_success = self.predictor.run_pipeline(empty_stream)
        self.assertFalse(is_success)

    def test_run_pipeline_valid_stream(self):
        random_bytes = "".join(random.choices(string.ascii_letters + string.digits, k=32)).encode('utf-8')
        valid_stream = io.BytesIO(random_bytes)
        is_success = self.predictor.run_pipeline(valid_stream)
        self.assertTrue(is_success)

    def test_functional_pipeline_empty_data_raises_value_error(self):
        with self.assertRaises(ValueError) as ctx:
            repo_health_predictor_pipeline({})
        self.assertEqual(str(ctx.exception), "Empty raw data")

    def test_functional_pipeline_execution_and_file_dump(self):
        repo_id = uuid.uuid4().hex
        raw_data = {"repository_id": repo_id, uuid.uuid4().hex: uuid.uuid4().hex}
        expected_score = 0.4242

        mock_file_instance = mock_open().return_value

        with patch('random.uniform', return_value=expected_score), \
             patch('os.makedirs') as mock_makedirs, \
             patch('builtins.open', mock_file_instance) as mock_file_open:

            result = repo_health_predictor_pipeline(raw_data)

        self.assertEqual(result["status"], "success")
        self.assertEqual(result["repository_id"], repo_id)
        self.assertAlmostEqual(result["prediction_score"], expected_score)

        mock_makedirs.assert_called_once_with("reports", exist_ok=True)
        expected_path = f"reports/health_prediction_{repo_id}.json"
        mock_file_open.assert_called_once_with(expected_path, "w", encoding="utf-8")

        written_data = "".join(call.args[0] for call in mock_file_instance.write.mock_calls)
        parsed_dump = json.loads(written_data)
        self.assertEqual(parsed_dump["repository_id"], repo_id)
        self.assertEqual(parsed_dump["prediction_score"], expected_score)


if __name__ == '__main__':
    unittest.main()