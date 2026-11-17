import unittest
import json
import io
import uuid
import random
from unittest.mock import patch, MagicMock
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    audit_repository,
    render_health_dashboard,
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
        invalid_metrics = [
            {"metric_name": "test", "score": "high", "timestamp": 123},
            {"metric_name": "test", "score": True, "timestamp": 123},
            {"metric_name": "test", "score": 105.0, "timestamp": 123}
        ]
        for m in invalid_metrics:
            with self.assertRaises(MetricValidationError):
                self.validator.validate(m)

    def test_validate_stream_parsing(self):
        random_id = uuid.uuid4().hex
        random_score = random.uniform(0, 100)
        data = [{"metric_name": random_id, "score": random_score, "timestamp": 123456789}]
        stream = io.StringIO(json.dumps(data))
        
        result = self.validator.validate_stream(stream)
        self.assertEqual(result[0]["metric_name"], random_id)
        self.assertEqual(result[0]["score"], random_score)

    def test_dispatch_and_validate_remote(self):
        random_url = f"http://{uuid.uuid4().hex}.com/api"
        payload = {"metric_name": uuid.uuid4().hex, "score": 50.0, "timestamp": 123}
        mock_response = {"status": "accepted", "id": uuid.uuid4().hex}
        
        with patch('requests.post') as mock_post:
            mock_post.return_value.json.return_value = mock_response
            result = self.validator.dispatch_and_validate_remote(payload, random_url)
            
            self.assertEqual(result, mock_response)
            mock_post.assert_called_once_with(random_url, json=payload)

    def test_audit_repository(self):
        payload = {
            "metric_name": uuid.uuid4().hex,
            "score": random.uniform(0, 100),
            "timestamp": random.randint(1000, 2000)
        }
        result = audit_repository(payload)
        self.assertEqual(result, payload)

    def test_render_health_dashboard(self):
        name = uuid.uuid4().hex
        score = random.randint(0, 100)
        payload = {"metric_name": name, "score": score}
        output = render_health_dashboard(payload)
        self.assertIn(name, output)
        self.assertIn(str(score), output)

    def test_validate_repo_health_metrics_normalization(self):
        run_id = uuid.uuid4().hex
        health_score = random.uniform(0, 100)
        payload = {"run_id": run_id, "health_score": health_score}
        
        result = validate_repo_health_metrics(payload)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], health_score)

    def test_validate_stream_bytes_decoding(self):
        random_data = [{"metric_name": "test", "score": 10.0, "timestamp": 1}]
        stream = io.BytesIO(json.dumps(random_data).encode('utf-8'))
        
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], "test")

    def test_validate_stream_invalid_json(self):
        stream = io.StringIO(uuid.uuid4().hex) # Garbage string
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

if __name__ == '__main__':
    unittest.main()