import unittest
from unittest.mock import patch
import random
import uuid
import string
import io
from skills.repo_health_analytics_transformer import RepoHealthAnalyticsэффициентTransformer, transform_health_metrics, RepoHealthTransformationError

class TestRepoHealthAnalyticsTransformer(unittest.TestCase):

    def setUp(self):
        self.transformer = RepoHealthAnalyticsэффициентTransformer()
        self.random_repo_id = str(uuid.uuid4())
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_status = random.choice(["HEALTHY", "WARNING", "CRITICAL", "UNKNOWN"])

    def test_transform_valid_metrics_success(self):
        input_data = {
            "repository_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: {
                    "score": self.random_score,
                    "status": self.random_status
                }
            },
            "timestamp": random.randint(1600000000, 1700000000)
        }

        result = self.transformer.transform(input_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_uuid"], self.random_repo_id)
        self.assertIn("normalized_metrics", result)
        self.assertEqual(
            result["normalized_metrics"][self.random_metric_name]["value"], 
            self.random_score
        )
        self.assertEqual(
            result["normalized_metrics"][self.random_metric_name]["severity"], 
            self.random_status
        )

    def test_transform_with_stream_input(self):
        raw_json_string = f'{{"repository_id": "{self.random_repo_id}", "score": {self.random_score}}}'
        stream_mock = io.BytesIO(raw_json_string.encode('utf-8'))

        with patch('skills.repo_health_analytics_transformer.json.load') as mock_json_load:
            mock_json_load.return_value = {
                "repository_id": self.random_repo_id,
                "metrics": {self.random_metric_name: {"score": self.random_score, "status": self.random_status}}
            }
            
            result = self.transformer.transform_stream(stream_mock)
            
            self.assertEqual(result["repo_uuid"], self.random_repo_id)
            mock_json_load.assert_called_once()

    def test_transform_invalid_data_raises_exception(self):
        malformed_data = {
            "bad_key": random.randint(1, 100),
            "random_hash": uuid.uuid4().hex
        }

        with self.assertRaises(RepoHealthTransformationError):
            self.transformer.transform(malformed_data)

    def test_module_level_transform_function(self):
        payload = {
            "repository_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: {
                    "score": self.random_score,
                    "status": self.random_status
                }
            }
        }

        output = transform_health_metrics(payload)
        self.assertEqual(output["repo_uuid"], self.random_repo_id)
        self.assertIn(self.random_metric_name, output["normalized_metrics"])

    def test_transformer_handles_random_noise_gracefully(self):
        noise_key = uuid.uuid4().hex
        noise_value = ''.join(random.choices(string.ascii_letters, k=15))
        
        input_data = {
            "repository_id": self.random_repo_id,
            "metrics": {
                self.random_metric_name: {
                    "score": self.random_score,
                    "status": self.random_status,
                    noise_key: noise_value
                }
            }
        }

        result = self.transformer.transform(input_data)
        transformed_item = result["normalized_metrics"][self.random_metric_name]
        
        self.assertEqual(transformed_item["value"], self.random_score)
        self.assertEqual(transformed_item["severity"], self.random_status)
        self.assertNotIn(noise_key, transformed_item)

if __name__ == '__main__':
    unittest.main()