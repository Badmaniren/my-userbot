import unittest
import json
import io
import random
import uuid
from unittest.mock import patch, MagicMock
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    validate_repo_health_metrics
)

class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()

    def test_validate_success(self):
        metric = {
            "metric_name": uuid.uuid4().hex,
            "score": random.uniform(0.0, 100.0),
            "timestamp": random.randint(1600000000, 1700000000)
        }
        self.assertTrue(self.validator.validate(metric))

    def test_validate_invalid_types(self):
        invalid_data = [
            {"metric_name": "test", "score": "high", "timestamp": 123},
            {"metric_name": "test", "score": True, "timestamp": 123},
            {"metric_name": "test", "score": 105.0, "timestamp": 123}
        ]
        for item in invalid_data:
            with self.assertRaises(MetricValidationError):
                self.validator.validate(item)

    def test_validate_stream_parsing(self):
        random_id = uuid.uuid4().hex
        random_score = random.uniform(0, 100)
        payload = [{"metric_name": random_id, "score": random_score, "timestamp": 1600000000}]
        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))

        result = self.validator.validate_stream(stream)
        self.assertEqual(result[0]["metric_name"], random_id)
        self.assertEqual(result[0]["score"], random_score)

    def test_validate_stream_invalid_json(self):
        stream = io.BytesIO(b"{invalid_json: true")
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_dispatch_and_validate_remote(self):
        url = f"https://{uuid.uuid4().hex}.com/api"
        payload = {"metric_name": uuid.uuid4().hex, "score": 50.0, "timestamp": 1600000000}
        expected_response = {"status": "accepted", "id": uuid.uuid4().hex}

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            result = self.validator.dispatch_and_validate_remote(payload, url)

            mock_post.assert_called_once_with(url, json=payload)
            self.assertEqual(result, expected_response)

    def test_validate_repo_health_metrics_normalization(self):
        # Проверка логики нормализации полей
        raw_data = {
            "health_score": random.uniform(0, 100),
            "run_id": uuid.uuid4().hex
        }

        result = validate_repo_health_metrics(raw_data)

        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], raw_data["health_score"])
        self.assertEqual(result["metrics"]["metric_name"], raw_data["run_id"])
        self.assertIn("timestamp", result["metrics"])

    def test_validate_repo_health_metrics_failure(self):
        # Передаем данные без обязательных полей после нормализации
        bad_data = {"random_key": uuid.uuid4().hex}
        result = validate_repo_health_metrics(bad_data)
        self.assertFalse(result["is_valid"])

    def test_stream_bytes_decoding_error(self):
        # Подача некорректных байтов для декодирования
        stream = io.BytesIO(b'\xff\xfe\xfd')
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

if __name__ == '__main__':
    unittest.main()