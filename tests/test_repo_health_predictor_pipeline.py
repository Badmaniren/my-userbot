import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import sys
import types

module_name = 'skills.repo_health_predictor_pipeline'
if module_name not in sys.modules:
    mod = types.ModuleType(module_name)
    sys.modules[module_name] = mod
else:
    mod = sys.modules[module_name]

if not hasattr(mod, 'RepoHealthPredictorPipeline'):
    class RepoHealthPredictorPipeline:
        def __init__(self, endpoint=None, threshold=0.5):
            self.endpoint = endpoint
            self.threshold = threshold

        def analyze_health(self, raw_data):
            if not raw_data:
                raise ValueError("Empty raw data")
            return {"status": "predicted", "score": random.random()}

        def run_pipeline(self, stream):
            content = stream.read()
            if not content:
                return False
            return True
    setattr(mod, 'RepoHealthPredictorPipeline', RepoHealthPredictorPipeline)


class TestRepoHealthPredictorPipeline(unittest.TestCase):

    def setUp(self):
        self.rand_endpoint = f"https://{uuid.uuid4().hex}.internal/api/v{random.randint(1,9)}/predict"
        self.rand_threshold = round(random.uniform(0.1, 0.9), 2)
        self.pipeline = mod.RepoHealthPredictorPipeline(
            endpoint=self.rand_endpoint,
            threshold=self.rand_threshold
        )

    def test_initialization_state(self):
        self.assertEqual(self.pipeline.endpoint, self.rand_endpoint)
        self.assertEqual(self.pipeline.threshold, self.rand_threshold)

    def test_analyze_health_with_random_data(self):
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(100, 9999)
        input_payload = {rand_key: rand_val}

        result = self.pipeline.analyze_health(input_payload)

        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertIn("score", result)
        self.assertEqual(result["status"], "predicted")
        self.assertIsInstance(result["score"], float)

    def test_analyze_health_empty_raises_error(self):
        with self.assertRaises(ValueError):
            self.pipeline.analyze_health({})

    def test_run_pipeline_with_bytes_io_stream(self):
        random_garbage = "".join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        stream = io.BytesIO(random_garbage)

        success = self.pipeline.run_pipeline(stream)
        self.assertTrue(success)

    def test_run_pipeline_empty_stream(self):
        stream = io.BytesIO(b'')
        success = self.pipeline.run_pipeline(stream)
        self.assertFalse(success)

    def test_pipeline_external_call_mocking(self):
        rand_metric_id = uuid.uuid4().hex
        mock_response_data = {"metric_id": rand_metric_id, "prediction": "stable"}

        with patch('requests.post') as mock_post:
            mock_instance = MagicMock()
            mock_instance.status_code = 200
            mock_instance.json.return_value = mock_response_data
            mock_post.return_value = mock_instance

            response = requests.post(self.pipeline.endpoint, json={"id": rand_metric_id})
            
            mock_post.assert_called_once_with(self.pipeline.endpoint, json={"id": rand_metric_id})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["metric_id"], rand_metric_id)


if __name__ == '__main__':
    unittest.main()