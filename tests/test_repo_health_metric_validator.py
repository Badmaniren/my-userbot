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
    validate_repo_health_metrics,
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
            "timestamp": self.timestamp,
        }
        result = self.validator.validate(payload)
        self.assertTrue(result)

    def test_validate_not_a_dictionary_raises_error(self):
        invalid_data = [random.randint(1, 100), uuid.uuid4().hex]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_metric_name_raises_error(self):
        payload = {
            "score": self.score,
            "timestamp": self.timestamp,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_missing_score_raises_error(self):
        payload = {
            "metric_name": self.metric_name,
            "timestamp": self.timestamp,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_missing_timestamp_raises_error(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_invalid_score_type_raises_error(self):
        payload = {
            "metric_name": self.metric_name,
            "score": uuid.uuid4().hex,
            "timestamp": self.timestamp,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_score_out_of_bounds_low_raises_error(self):
        payload = {
            "metric_name": self.metric_name,
            "score": -random.uniform(0.1, 50.0),
            "timestamp": self.timestamp,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_score_out_of_bounds_high_raises_error(self):
        payload = {
            "metric_name": self.metric_name,
            "score": 100.0 + random.uniform(0.1, 50.0),
            "timestamp": self.timestamp,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_stream_with_bytes(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp,
        }
        raw_data = json.dumps(payload).encode("utf-8")
        stream = io.BytesIO(raw_data)
        results = self.validator.validate_stream(stream)
        self.assertIsInstance(results, list)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metric_name"], self.metric_name)

    def test_validate_stream_with_string_io(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp,
        }
        raw_data = json.dumps(payload)
        stream = io.StringIO(raw_data)
        results = self.validator.validate_stream(stream)
        self.assertEqual(results[0]["score"], self.score)

    def test_validate_stream_invalid_json_raises_error(self):
        bad_content = uuid.uuid4().hex + "{"
        stream = io.StringIO(bad_content)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_validate_stream_invalid_bytes_decode_raises_error(self):
        bad_bytes = b'\xff\xfe\x00\x00invalid_bytes_' + uuid.uuid4().bytes
        stream = io.BytesIO(bad_bytes)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://{uuid.uuid4().hex}.example.com/api/v1/metrics"
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp,
        }
        expected_response = {"status": "ok", "id": uuid.uuid4().hex}

        mock_response = MagicMock()
        mock_response.json.return_value = expected_response

        with patch("requests.post", return_value=mock_response) as mock_post:
            resp = self.validator.dispatch_and_validate_remote(payload, endpoint)
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(resp, expected_response)

    def test_audit_repository_stub(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
        }
        res = audit_repository(payload)
        self.assertEqual(res, payload)

    def test_render_health_dashboard_stub(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
        }
        res = render_health_dashboard(payload)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_wrapper_valid(self):
        payload = {
            "health_score": self.score,
            "run_id": self.metric_name,
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertIn("metrics", res)

    def test_validate_repo_health_metrics_wrapper_invalid(self):
        payload = {
            "health_score": uuid.uuid4().hex,
            "run_id": self.metric_name,
        }
        res = validate_repo_health_metrics(payload)
        self.assertFalse(res["is_valid"])


if __name__ == "__main__":
    unittest.main()