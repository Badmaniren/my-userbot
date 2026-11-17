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
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        result = self.validator.validate(payload)
        self.assertTrue(result)

    def test_validate_not_a_dict(self):
        invalid_payload = f"not_a_dict_{uuid.uuid4().hex}"
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_payload)
        self.assertIn("must be a dictionary", str(ctx.exception))

    def test_validate_missing_mandatory_fields(self):
        base_payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        for field in ["metric_name", "score", "timestamp"]:
            payload = base_payload.copy()
            del payload[field]
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(payload)
            self.assertIn(f"Missing mandatory field: '{field}'", str(ctx.exception))

    def test_validate_invalid_score_type(self):
        for invalid_score in [f"score_{uuid.uuid4().hex[:4]}", True, False, None, [self.score]]:
            payload = {
                "metric_name": self.metric_name,
                "score": invalid_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(payload)
            self.assertIn("Score must be a number", str(ctx.exception))

    def test_validate_score_out_of_bounds(self):
        for invalid_score in [-random.uniform(0.1, 100.0), 100.1 + random.uniform(0.0, 50.0)]:
            payload = {
                "metric_name": self.metric_name,
                "score": invalid_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(payload)
            self.assertIn("score is out of bounds", str(ctx.exception))

    def test_validate_stream_with_string(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        stream_data = json.dumps(payload)
        result = self.validator.validate_stream(stream_data)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)
        self.assertEqual(result[0]["score"], self.score)

    def test_validate_stream_with_bytes_io(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        stream_bytes = json.dumps(payload).encode('utf-8')
        stream = io.BytesIO(stream_bytes)
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)

    def test_validate_stream_invalid_bytes_decode(self):
        invalid_bytes = b'\xff\xfe\xfd' + uuid.uuid4().bytes
        stream = io.BytesIO(invalid_bytes)
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(stream)
        self.assertIn("Failed to decode stream bytes", str(ctx.exception))

    def test_validate_stream_invalid_json(self):
        corrupted_data = f"{{invalid_json_{uuid.uuid4().hex}}}"
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(corrupted_data)
        self.assertIn("Failed to parse JSON", str(ctx.exception))

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://{uuid.uuid4().hex}.test/api/v1/metrics"
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        expected_response = {"status": "success", "token": uuid.uuid4().hex}

        with patch("skills.repo_health_metric_validator.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            response = self.validator.dispatch_and_validate_remote(payload, endpoint)

            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(response, expected_response)

    def test_audit_repository_success(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        res = audit_repository(payload)
        self.assertEqual(res, payload)

    def test_audit_repository_failure(self):
        payload = {
            "metric_name": self.metric_name,
            "score": -5.0,
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            audit_repository(payload)

    def test_render_health_dashboard(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        dashboard_str = render_health_dashboard(payload)
        self.assertIn(self.metric_name, dashboard_str)
        self.assertIn(str(self.score), dashboard_str)

    def test_render_health_dashboard_empty(self):
        dashboard_str = render_health_dashboard({})
        self.assertIn("unknown", dashboard_str)
        self.assertIn("0", dashboard_str)

    def test_validate_repo_health_metrics_normalized_valid(self):
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        health_score = round(random.uniform(1.0, 99.0), 2)
        payload = {
            "run_id": run_id,
            "health_score": health_score,
            "timestamp": self.timestamp
        }
        result = validate_repo_health_metrics(payload)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], health_score)
        self.assertEqual(result["metrics"]["timestamp"], self.timestamp)

    def test_validate_repo_health_metrics_normalized_invalid(self):
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        invalid_score = 150.0
        payload = {
            "metric_name": run_id,
            "score": invalid_score,
            "timestamp": self.timestamp
        }
        result = validate_repo_health_metrics(payload)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], invalid_score)


if __name__ == "__main__":
    unittest.main()