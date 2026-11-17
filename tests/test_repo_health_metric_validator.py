import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import string

from skills.repo_health_metric_validator import (
    MetricValidationError,
    RepoHealthMetricValidator,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics,
)


class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.1, 99.9), 2)
        self.random_timestamp = random.randint(1500000000, 1700000000)
        self.random_url = f"https://{uuid.uuid4().hex[:8]}.test/endpoint"

    def test_validate_success(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(metric_data)
        self.assertTrue(result)

    def test_validate_not_a_dict(self):
        invalid_data = [self.random_metric_name, self.random_score]
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate(invalid_data)
        self.assertIn("Metric data must be a dictionary", str(ctx.exception))

    def test_validate_missing_mandatory_fields(self):
        base_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        for field in ["metric_name", "score", "timestamp"]:
            corrupt_data = base_data.copy()
            del corrupt_data[field]
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(corrupt_data)
            self.assertIn(f"Missing mandatory field: '{field}'", str(ctx.exception))

    def test_validate_invalid_score_types(self):
        invalid_scores = [
            uuid.uuid4().hex[:5],
            True,
            False,
            None,
            [self.random_score],
            {"score": self.random_score}
        ]
        for bad_score in invalid_scores:
            metric_data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(metric_data)
            self.assertIn("Score must be a number", str(ctx.exception))

    def test_validate_score_out_of_bounds(self):
        out_of_bounds = [
            random.uniform(-100.0, -0.01),
            random.uniform(100.01, 500.0)
        ]
        for bad_score in out_of_bounds:
            metric_data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(metric_data)
            self.assertIn("score is out of bounds [0.0, 100.0]", str(ctx.exception))

    def test_validate_stream_bytes_io(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        json_bytes = json.dumps(metric_data).encode('utf-8')
        stream = io.BytesIO(json_bytes)
        
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.random_metric_name)
        self.assertEqual(result[0]["score"], self.random_score)

    def test_validate_stream_string(self):
        metric_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        json_str = json.dumps(metric_data)
        
        result = self.validator.validate_stream(json_str)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.random_metric_name)

    def test_validate_stream_invalid_bytes_decode(self):
        bad_bytes = b'\xff\xfe\xfd'
        stream = io.BytesIO(bad_bytes)
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(stream)
        self.assertIn("Failed to decode stream bytes", str(ctx.exception))

    def test_validate_stream_invalid_json(self):
        bad_json = "".join(random.choices(string.ascii_letters, k=15))
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(bad_json)
        self.assertIn("Failed to parse JSON", str(ctx.exception))

    def test_dispatch_and_validate_remote(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        expected_response = {
            "status": uuid.uuid4().hex[:6],
            "accepted": True
        }

        with patch("skills.repo_health_metric_validator.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            res = self.validator.dispatch_and_validate_remote(payload, self.random_url)
            
            mock_post.assert_called_once_with(self.random_url, json=payload)
            self.assertEqual(res, expected_response)

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

    def test_validate_repo_health_metrics_success(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], self.random_metric_name)
        self.assertEqual(res["metrics"]["score"], self.random_score)

    def test_validate_repo_health_metrics_normalization(self):
        health_score = round(random.uniform(0.0, 100.0), 2)
        run_id = uuid.uuid4().hex[:10]
        payload = {
            "health_score": health_score,
            "run_id": run_id
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], health_score)
        self.assertEqual(res["metrics"]["metric_name"], run_id)
        self.assertEqual(res["metrics"]["timestamp"], 1600000000)

    def test_validate_repo_health_metrics_failure(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": uuid.uuid4().hex[:5],
            "timestamp": self.random_timestamp
        }
        res = validate_repo_health_metrics(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"], payload)


if __name__ == "__main__":
    unittest.main()