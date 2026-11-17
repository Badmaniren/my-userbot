import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
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
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.score = round(random.uniform(0.0, 100.0), 2)
        self.timestamp = random.randint(1500000000, 1800000000)

    def test_validate_success(self):
        valid_metric = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        result = self.validator.validate(valid_metric)
        self.assertTrue(result)

    def test_validate_not_a_dict_raises_error(self):
        invalid_data = [uuid.uuid4().hex, random.randint(1, 100)]
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("Metric data must be a dictionary", str(ctx.exception))

    def test_validate_missing_mandatory_fields(self):
        base_data = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        for field in ["metric_name", "score", "timestamp"]:
            corrupted_data = base_data.copy()
            del corrupted_data[field]
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(corrupted_data)
            self.assertIn(f"Missing mandatory field: '{field}'", str(ctx.exception))

    def test_validate_invalid_score_types(self):
        invalid_scores = [uuid.uuid4().hex, True, False, None, [self.score]]
        for bad_score in invalid_scores:
            metric_data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(metric_data)
            self.assertIn("Score must be a number", str(ctx.exception))

    def test_validate_score_out_of_bounds(self):
        out_of_bounds = [
            random.uniform(-100.0, -0.01),
            random.uniform(100.01, 200.0)
        ]
        for bad_score in out_of_bounds:
            metric_data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(metric_data)
            self.assertIn("score is out of bounds", str(ctx.exception))

    def test_validate_stream_with_io_bytes(self):
        metric_list = [{
            "metric_name": f"metric_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }]
        json_bytes = json.dumps(metric_list).encode('utf-8')
        stream = io.BytesIO(json_bytes)

        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], metric_list[0]["metric_name"])

    def test_validate_stream_with_unicode_decode_error(self):
        bad_bytes = b'\xff\xfe\xfd ' + uuid.uuid4().hex.encode('utf-8')
        stream = io.BytesIO(bad_bytes)

        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(stream)
        self.assertIn("Failed to decode stream bytes", str(ctx.exception))

    def test_validate_stream_with_invalid_json(self):
        corrupted_json = f"{{invalid_json_{uuid.uuid4().hex}}}"
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(corrupted_json)
        self.assertIn("Failed to parse JSON", str(ctx.exception))

    def test_validate_stream_single_dict(self):
        single_metric = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        json_str = json.dumps(single_metric)
        result = self.validator.validate_stream(json_str)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], self.score)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://{uuid.uuid4().hex}.example.com/api/v1/metrics"
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp,
            "tracking_id": uuid.uuid4().hex
        }
        mock_response_data = {
            "status": "success",
            "ack_id": uuid.uuid4().hex
        }

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            response = self.validator.dispatch_and_validate_remote(payload, endpoint)
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(response, mock_response_data)

    def test_audit_repository(self):
        metrics = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        res = audit_repository(metrics)
        self.assertEqual(res, metrics)

    def test_render_health_dashboard(self):
        metrics = {
            "metric_name": self.metric_name,
            "score": self.score
        }
        res = render_health_dashboard(metrics)
        self.assertEqual(res, "dashboard_output.html")

    def test_validate_repo_health_metrics_normalization(self):
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        health_score = round(random.uniform(0.0, 100.0), 2)
        raw_metrics = {
            "run_id": run_id,
            "health_score": health_score
        }

        result = validate_repo_health_metrics(raw_metrics)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], health_score)
        self.assertEqual(result["metrics"]["timestamp"], 1600000000)

    def test_validate_repo_health_metrics_invalid(self):
        invalid_metrics = {
            "metric_name": self.metric_name,
            "score": -999.99,
            "timestamp": self.timestamp
        }
        result = validate_repo_health_metrics(invalid_metrics)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], -999.99)