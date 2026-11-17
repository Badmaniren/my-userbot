import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
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
        self.metric_name_val = uuid.uuid4().hex
        self.score_val = round(random.uniform(1.0, 99.0), 2)
        self.timestamp_val = random.randint(1000000000, 2000000000)

    def test_validate_success(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }
        res = self.validator.validate(payload)
        self.assertTrue(res)

    def test_validate_not_a_dict(self):
        bad_payload = uuid.uuid4().hex
        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload) # type: ignore

    def test_validate_missing_metric_name(self):
        payload = {
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_missing_score(self):
        payload = {
            "metric_name": self.metric_name_val,
            "timestamp": self.timestamp_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_missing_timestamp(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": self.score_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_invalid_score_type(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": uuid.uuid4().hex,
            "timestamp": self.timestamp_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_score_is_boolean(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": True,
            "timestamp": self.timestamp_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_score_out_of_bounds_low(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": -0.01,
            "timestamp": self.timestamp_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_score_out_of_bounds_high(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": 100.01,
            "timestamp": self.timestamp_val
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

    def test_validate_stream_bytes_success(self):
        payload = [{
            "metric_name": self.metric_name_val,
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }]
        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name_val)

    def test_validate_stream_str_success(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }
        stream_str = json.dumps(payload)
        result = self.validator.validate_stream(stream_str)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], self.score_val)

    def test_validate_stream_decode_error(self):
        bad_bytes = b'\xff\xfe\xfd'
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_bytes)

    def test_validate_stream_json_decode_error(self):
        bad_stream = io.BytesIO(b"{invalid_json")
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_stream)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"http://{uuid.uuid4().hex}.local/api"
        payload = {
            "metric_name": self.metric_name_val,
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }
        expected_response = {"status": uuid.uuid4().hex}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            resp = self.validator.dispatch_and_validate_remote(payload, endpoint)
            self.assertEqual(resp, expected_response)
            mock_post.assert_called_once_with(endpoint, json=payload)

    def test_audit_repository(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }
        res = audit_repository(payload)
        self.assertEqual(res, payload)

    def test_render_health_dashboard(self):
        payload = {
            "metric_name": self.metric_name_val,
            "score": self.score_val,
            "timestamp": self.timestamp_val
        }
        res = render_health_dashboard(payload)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_valid_normalization(self):
        payload = {
            "health_score": self.score_val,
            "run_id": self.metric_name_val
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], self.score_val)
        self.assertEqual(res["metrics"]["metric_name"], self.metric_name_val)
        self.assertEqual(res["metrics"]["timestamp"], 1600000000)

    def test_validate_repo_health_metrics_invalid(self):
        payload = {
            "health_score": 150.0,
            "run_id": self.metric_name_val
        }
        res = validate_repo_health_metrics(payload)
        self.assertFalse(res["is_valid"])

if __name__ == '__main__':
    unittest.main()