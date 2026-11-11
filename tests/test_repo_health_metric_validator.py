import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
import requests

from skills.repo_health_metric_validator import (
    MetricValidationError,
    RepoHealthMetricValidator,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics
)


class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1700000000)

    def test_validate_success(self):
        valid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(valid_data)
        self.assertTrue(result)

    def test_validate_not_a_dictionary_raises_error(self):
        invalid_data = [self.random_metric_name, self.random_score]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_metric_name_raises_error(self):
        invalid_data = {
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_score_raises_error(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_timestamp_raises_error(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_score_not_a_number_raises_error(self):
        invalid_score_str = f"score_{uuid.uuid4().hex[:6]}"
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": invalid_score_str,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds_low_raises_error(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": -random.uniform(0.01, 50.0),
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds_high_raises_error(self):
        invalid_data = {
            "metric_name": self.random_metric_name,
            "score": 100.0 + random.uniform(0.01, 50.0),
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_stream_bytes_success(self):
        payload = [{
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }]
        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.random_metric_name)
        self.assertEqual(result[0]["score"], self.random_score)

    def test_validate_stream_invalid_utf8_raises_error(self):
        invalid_bytes = b'\xff\xfe\xfd ' + uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(invalid_bytes)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_validate_stream_invalid_json_raises_error(self):
        corrupted_json = f"not_a_json_{uuid.uuid4().hex}"
        stream = io.StringIO(corrupted_json)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://{uuid.uuid4().hex}.example.com/api/v1/metrics"
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        mock_response_data = {"status": uuid.uuid4().hex, "acknowledged": True}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            response = self.validator.dispatch_and_validate_remote(payload, endpoint)

            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(response, mock_response_data)

    def test_audit_repository_stub(self):
        data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = audit_repository(data)
        self.assertEqual(result, data)

    def test_render_health_dashboard_stub(self):
        data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = render_health_dashboard(data)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_validate_repo_health_metrics_success(self):
        data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = validate_repo_health_metrics(data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], self.random_score)

    def test_validate_repo_health_metrics_normalized_fields(self):
        health_score = round(random.uniform(0.0, 100.0), 2)
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        data = {
            "health_score": health_score,
            "run_id": run_id
        }
        result = validate_repo_health_metrics(data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], health_score)
        self.assertEqual(result["metrics"]["metric_name"], run_id)

    def test_validate_repo_health_metrics_invalid(self):
        invalid_score = 150.0 + random.uniform(1.0, 10.0)
        data = {
            "metric_name": self.random_metric_name,
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }
        result = validate_repo_health_metrics(data)
        self.assertFalse(result["is_valid"])


if __name__ == "__main__":
    unittest.main()