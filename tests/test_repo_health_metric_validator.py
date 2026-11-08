import unittest
from unittest.mock import patch, MagicMock
import io
import json
import random
import uuid
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
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.score = round(random.uniform(0.0, 100.0), 2)
        self.timestamp = random.randint(1500000000, 1800000000)

    def test_validate_success(self):
        valid_data = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        result = self.validator.validate(valid_data)
        self.assertTrue(result)

    def test_validate_not_a_dictionary_raises_error(self):
        invalid_data = [uuid.uuid4().hex, random.randint(1, 100)]
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("must be a dictionary", str(ctx.exception))

    def test_validate_missing_mandatory_fields(self):
        mandatory_fields = ["metric_name", "score", "timestamp"]
        for field in mandatory_fields:
            data = {
                "metric_name": self.metric_name,
                "score": self.score,
                "timestamp": self.timestamp
            }
            del data[field]
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(data)
            self.assertIn(f"Missing mandatory field: '{field}'", str(ctx.exception))

    def test_validate_score_not_a_number_raises_error(self):
        invalid_scores = [uuid.uuid4().hex, None, [self.score], {"val": self.score}]
        for invalid_score in invalid_scores:
            data = {
                "metric_name": self.metric_name,
                "score": invalid_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(data)
            self.assertIn("Score must be a number", str(ctx.exception))

    def test_validate_score_out_of_bounds_raises_error(self):
        out_of_bounds = [
            round(random.uniform(-100.0, -0.01), 2),
            round(random.uniform(100.01, 1000.0), 2)
        ]
        for bad_score in out_of_bounds:
            data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(data)
            self.assertIn("score is out of bounds", str(ctx.exception))

    def test_validate_stream_with_bytes_success(self):
        metric_dict = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        json_bytes = json.dumps(metric_dict).encode('utf-8')
        stream = io.BytesIO(json_bytes)
        
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)
        self.assertEqual(result[0]["score"], self.score)

    def test_validate_stream_with_invalid_unicode_bytes_raises_error(self):
        bad_bytes = b'\xff\xfe\xfd ' + uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(bad_bytes)
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(stream)
        self.assertIn("Failed to decode stream bytes", str(ctx.exception))

    def test_validate_stream_with_invalid_json_raises_error(self):
        corrupted_content = f"{{invalid_json_{uuid.uuid4().hex}}}"
        stream = io.StringIO(corrupted_content)
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(stream)
        self.assertIn("Failed to parse JSON", str(ctx.exception))

    def test_dispatch_and_validate_remote_success(self):
        endpoint = f"https://{uuid.uuid4().hex}.example.com/api/v1/metrics"
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        expected_response_data = {
            "status": "success",
            "received_id": uuid.uuid4().hex
        }

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response_data
            mock_post.return_value = mock_response

            response = self.validator.dispatch_and_validate_remote(payload, endpoint)
            
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(response, expected_response_data)

    def test_audit_repository_stub(self):
        data = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        res = audit_repository(data)
        self.assertEqual(res, data)

    def test_render_health_dashboard_stub(self):
        data = {
            "metric_name": self.metric_name,
            "score": self.score
        }
        res = render_health_dashboard(data)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_normalization_and_validity(self):
        health_score = round(random.uniform(0.0, 100.0), 2)
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        
        raw_metrics = {
            "health_score": health_score,
            "run_id": run_id
        }

        result = validate_repo_health_metrics(raw_metrics)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"], raw_metrics)

    def test_validate_repo_health_metrics_invalid_data(self):
        bad_score = round(random.uniform(101.0, 500.0), 2)
        raw_metrics = {
            "health_score": bad_score,
            "run_id": f"run_{uuid.uuid4().hex[:6]}"
        }

        result = validate_repo_health_metrics(raw_metrics)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"], raw_metrics)