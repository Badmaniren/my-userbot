import unittest
from unittest.mock import patch, mock_open
import os
import json
import uuid
import random
import io
from skills.repo_health_predictor_pipeline import RepoHealthPredictorPipeline, repo_health_predictor_pipeline


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def test_init_default_attributes(self):
        endpoint_val = uuid.uuid4().hex
        threshold_val = round(random.uniform(0.1, 0.9), 2)
        pipeline = RepoHealthPredictorPipeline(endpoint=endpoint_val, threshold=threshold_val)
        self.assertEqual(pipeline.endpoint, endpoint_val)
        self.assertEqual(pipeline.threshold, threshold_val)

    def test_analyze_health_empty_data_raises_value_error(self):
        pipeline = RepoHealthPredictorPipeline()
        with self.assertRaises(ValueError):
            pipeline.analyze_health({})

    def test_analyze_health_success(self):
        pipeline = RepoHealthPredictorPipeline()
        raw_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = pipeline.analyze_health(raw_data)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "predicted")
        self.assertIn("score", result)
        self.assertIsInstance(result["score"], float)

    def test_run_pipeline_empty_stream(self):
        pipeline = RepoHealthPredictorPipeline()
        empty_stream = io.BytesIO(b"")
        result = pipeline.run_pipeline(empty_stream)
        self.assertFalse(result)

    def test_run_pipeline_non_empty_stream(self):
        pipeline = RepoHealthPredictorPipeline()
        random_bytes = uuid.uuid4().bytes
        stream = io.BytesIO(random_bytes)
        result = pipeline.run_pipeline(stream)
        self.assertTrue(result)

    def test_functional_pipeline_execution_and_file_dump(self):
        repo_id = uuid.uuid4().hex
        raw_data = {"repository_id": repo_id, uuid.uuid4().hex: random.randint(1, 100)}

        mock_file_handle = mock_open()
        with patch("os.makedirs") as mock_makedirs, \
             patch("builtins.open", mock_file_handle):

            result = repo_health_predictor_pipeline(raw_data)

            mock_makedirs.assert_called_once_with("reports", exist_ok=True)
            expected_path = f"reports/health_prediction_{repo_id}.json"
            mock_file_handle.assert_called_once_with(expected_path, "w", encoding="utf-8")

            handle = mock_file_handle()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            
            parsed_dump = json.loads(written_data)
            self.assertEqual(parsed_dump["repository_id"], repo_id)
            self.assertEqual(parsed_dump["status"], "success")
            self.assertIn("prediction_score", parsed_dump)
            self.assertEqual(result, parsed_dump)

    def test_repo_health_predictor_pipeline_empty_data_raises(self):
        with self.assertRaises(ValueError):
            repo_health_predictor_pipeline({})


if __name__ == "__main__":
    unittest.main()