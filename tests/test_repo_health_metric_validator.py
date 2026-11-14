import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
import string
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
        self.random_timestamp = random.randint(1000000000, 2000000000)
        self.random_endpoint = f"https://{uuid.uuid4().hex[:8]}.com/api/v1/metrics"

    def test_validate_success(self):
        valid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(valid_data)
        self.assertTrue(result)

    def test_validate_not_a_dict(self):
        invalid_data = [self.random_metric_name, self.random_score]
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

    def test_validate_invalid_score_type(self):
        invalid_types = [uuid.uuid4().hex, True, False, None, [10], {"val": 10}]
        for bad_score in invalid_types:
            invalid_data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds(self):
        bad_scores = [-0.01, -100.0, 100.01, 9999.9]
        for bad_score in bad_scores:
            invalid_data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_stream_valid_io_bytes(self):
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

    def test_validate_stream_valid_string(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        stream_str = json.dumps(payload)
        result = self.validator.validate_stream(stream_str)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], self.random_score)

    def test_validate_stream_invalid_bytes_decode(self):
        bad_bytes = b'\xff\xfe\xfd corrupt bytes ' + uuid.uuid4().bytes
        stream = io.BytesIO(bad_bytes)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_validate_stream_invalid_json(self):
        bad_json = f"{{ invalid_json_syntax: {uuid.uuid4().hex} }}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_json)

    def test_dispatch_and_validate_remote(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        mock_response_data = {"status": uuid.uuid4().hex, "acknowledged": True}

        with patch('requests.post') as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            resp = self.validator.dispatch_and_validate_remote(payload, self.random_endpoint)

            mock_post.assert_called_once_with(self.random_endpoint, json=payload)
            self.assertEqual(resp, mock_response_data)

    def test_audit_repository(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        res = audit_repository(payload)
        self.assertEqual(res, payload)

    def test_render_health_dashboard(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        res = render_health_dashboard(payload)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_normalization_and_validity(self):
        health_score_val = round(random.uniform(1.0, 99.0), 2)
        run_id_val = f"run_{uuid.uuid4().hex[:6]}"
        
        input_data = {
            "health_score": health_score_val,
            "run_id": run_id_val
        }

        result = validate_repo_health_metrics(input_data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], health_score_val)
        self.assertEqual(result["metrics"]["metric_name"], run_id_val)
        self.assertIn("timestamp", result["metrics"])

    def test_validate_repo_health_metrics_invalid(self):
        input_data = {
            "score": 999.99,
            "metric_name": self.random_metric_name,
            "timestamp": self.random_timestamp
        }

        result = validate_repo_health_metrics(input_data)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], 999.99)