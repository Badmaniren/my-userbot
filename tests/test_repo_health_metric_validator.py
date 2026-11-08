import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
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
        self.random_metric_name = uuid.uuid4().hex
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)
        self.random_url = f"https://{uuid.uuid4().hex}.com/api/v1/metrics"

    def test_validate_success(self):
        valid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(valid_data)
        self.assertTrue(result)

    def test_validate_not_a_dict(self):
        invalid_data = [uuid.uuid4().hex, random.randint(1, 100)]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_metric_name(self):
        invalid_data = {
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("metric_name", str(ctx.exception))

    def test_validate_missing_score(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("score", str(ctx.exception))

    def test_validate_missing_timestamp(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score
        }
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("timestamp", str(ctx.exception))

    def test_validate_score_type_invalid(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": uuid.uuid4().hex,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("Score must be a number", str(ctx.exception))

    def test_validate_score_out_of_bounds_low(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": -random.uniform(0.1, 50.0),
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("out of bounds", str(ctx.exception))

    def test_validate_score_out_of_bounds_high(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": 100.0 + random.uniform(0.1, 50.0),
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("out of bounds", str(ctx.exception))

    def test_validate_stream_bytes(self):
        metric_item = {
            "metric_name": uuid.uuid4().hex,
            "score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        stream_content = json.dumps(metric_item).encode('utf-8')
        mock_stream = io.BytesIO(stream_content)
        
        result = self.validator.validate_stream(mock_stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], metric_item["metric_name"])

    def test_validate_stream_string(self):
        metric_item = {
            "metric_name": uuid.uuid4().hex,
            "score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        stream_content = json.dumps(metric_item)
        
        result = self.validator.validate_stream(stream_content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], metric_item["score"])

    def test_validate_stream_malformed_payload(self):
        malformed_bytes = b'\xb3\xff\x00invalid_garbage_stream'
        mock_stream = io.BytesIO(malformed_bytes)
        
        with self.assertRaises((UnicodeDecodeError, json.JSONDecodeError, MetricValidationError)):
            self.validator.validate_stream(mock_stream)

    def test_dispatch_and_validate_remote(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        mock_response_data = {"status": uuid.uuid4().hex, "accepted": True}

        with patch("requests.post") as mock_post:
            instance = mock_post.return_value
            instance.json.return_value = mock_response_data

            response = self.validator.dispatch_and_validate_remote(payload, self.random_url)
            mock_post.assert_called_once_with(self.random_url, json=payload)
            self.assertEqual(response, mock_response_data)

    def test_audit_repository_stub(self):
        data = {uuid.uuid4().hex: uuid.uuid4().hex}
        result = audit_repository(data)
        self.assertEqual(result, data)

    def test_render_health_dashboard_stub(self):
        data = {uuid.uuid4().hex: random.randint(1, 100)}
        result = render_health_dashboard(data)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_validate_repo_health_metrics_wrapper_valid(self):
        raw_data = {
            "health_score": round(random.uniform(0.0, 100.0), 2),
            "run_id": uuid.uuid4().hex
        }
        res = validate_repo_health_metrics(raw_data)
        self.assertTrue(res["is_valid"])
        self.assertIn("metrics", res)

    def test_validate_repo_health_metrics_wrapper_invalid(self):
        raw_data = {
            "health_score": random.uniform(105.0, 200.0),
            "run_id": uuid.uuid4().hex
        }
        res = validate_repo_health_metrics(raw_data)
        self.assertFalse(res["is_valid"])


if __name__ == "__main__":
    unittest.main()