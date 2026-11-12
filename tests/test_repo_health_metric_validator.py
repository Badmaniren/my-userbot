import unittest
from unittest.mock import patch, MagicMock
import json
import io
import uuid
import random
import string
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
        self.random_timestamp = random.randint(1500000000, 1900000000)

    def test_validate_success(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(metric_data)
        self.assertTrue(result)

    def test_validate_not_dict(self):
        with self.assertRaises(MetricValidationError):
            self.validator.validate(f"not_a_dict_{uuid.uuid4().hex}")

    def test_validate_missing_metric_name(self):
        metric_data = {
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric_data)

    def test_validate_missing_score(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric_data)

    def test_validate_missing_timestamp(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric_data)

    def test_validate_invalid_score_type(self):
        invalid_scores = [
            f"score_{uuid.uuid4().hex[:4]}",
            True,
            False,
            None,
            [],
            {}
        ]
        for score in invalid_scores:
            metric_data = {
                "metric_name": self.random_metric_name,
                "score": score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(metric_data)

    def test_validate_score_out_of_bounds(self):
        out_of_bounds = [
            random.uniform(-100.0, -0.01),
            random.uniform(100.01, 200.0)
        ]
        for score in out_of_bounds:
            metric_data = {
                "metric_name": self.random_metric_name,
                "score": score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(metric_data)

    def test_validate_stream_with_bytes(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        payload = json.dumps(metric_data).encode('utf-8')
        stream = io.BytesIO(payload)
        
        result = self.validator.validate_stream(stream)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.random_metric_name)

    def test_validate_stream_with_string_io(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        payload = json.dumps([metric_data])
        stream = io.StringIO(payload)
        
        result = self.validator.validate_stream(stream)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], self.random_score)

    def test_validate_stream_with_raw_string(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        payload = json.dumps(metric_data)
        
        result = self.validator.validate_stream(payload)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["timestamp"], self.random_timestamp)

    def test_validate_stream_decoding_error(self):
        bad_bytes = b'\xff\xfe\xfd' + uuid.uuid4().bytes
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_bytes)

    def test_validate_stream_json_decode_error(self):
        bad_json = f"not_json_{uuid.uuid4().hex}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_json)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://{uuid.uuid4().hex[:10]}.net/api/v1/{uuid.uuid4().hex[:6]}"
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "session": uuid.uuid4().hex
        }
        expected_response = {
            "status": "success",
            "ack_id": uuid.uuid4().hex
        }

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            response = self.validator.dispatch_and_validate_remote(payload, endpoint)
            
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(response, expected_response)

    def test_audit_repository(self):
        metrics_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "audit_tag": uuid.uuid4().hex
        }
        result = audit_repository(metrics_data)
        self.assertEqual(result, metrics_data)

    def test_render_health_dashboard(self):
        metrics_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = render_health_dashboard(metrics_data)
        self.assertIsInstance(result, str)
        self.assertTrue(len(result) > 0)

    def test_validate_repo_health_metrics_success(self):
        metrics_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = validate_repo_health_metrics(metrics_data)
        self.assertIsInstance(result, dict)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], self.random_metric_name)

    def test_validate_repo_health_metrics_normalization(self):
        raw_score = round(random.uniform(0.0, 100.0), 2)
        raw_run_id = f"run_{uuid.uuid4().hex[:8]}"
        
        metrics_data = {
            "health_score": raw_score,
            "run_id": raw_run_id
        }
        result = validate_repo_health_metrics(metrics_data)
        self.assertIsInstance(result, dict)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], raw_score)
        self.assertEqual(result["metrics"]["metric_name"], raw_run_id)
        self.assertIn("timestamp", result["metrics"])

    def test_validate_repo_health_metrics_failure(self):
        metrics_data = {
            "metric_name": self.random_metric_name,
            "score": random.uniform(105.0, 500.0),
            "timestamp": self.random_timestamp
        }
        result = validate_repo_health_metrics(metrics_data)
        self.assertIsInstance(result, dict)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], self.random_metric_name)


if __name__ == "__main__":
    unittest.main()