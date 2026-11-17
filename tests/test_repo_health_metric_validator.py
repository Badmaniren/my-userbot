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
    validate_repo_health_metrics,
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

    def test_validate_not_a_dict(self):
        invalid_data = [self.metric_name, self.score]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_metric_name(self):
        invalid_data = {
            "score": self.score,
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_score(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_timestamp(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "score": self.score
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_invalid_score_type(self):
        invalid_scores = [f"score_{uuid.uuid4().hex[:4]}", True, False, None, {}]
        for bad_score in invalid_scores:
            invalid_data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds(self):
        out_of_bounds = [-random.uniform(0.1, 1000.0), 100.0 + random.uniform(0.1, 1000.0)]
        for bad_score in out_of_bounds:
            invalid_data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_stream_valid_json_string(self):
        payload = [{
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }]
        stream_content = json.dumps(payload)
        result = self.validator.validate_stream(stream_content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)
        self.assertEqual(result[0]["score"], self.score)

    def test_validate_stream_valid_io_bytes(self):
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        stream_content = io.BytesIO(json.dumps(payload).encode('utf-8'))
        result = self.validator.validate_stream(stream_content)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)

    def test_validate_stream_decode_error(self):
        bad_bytes = b'\xff\xfe\x00\x01 invalid bytes ' + uuid.uuid4().bytes
        stream_content = io.BytesIO(bad_bytes)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream_content)

    def test_validate_stream_json_decode_error(self):
        bad_json = "".join(random.choices(string.ascii_letters, k=15)) + " {invalid_json} "
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_json)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"http://{uuid.uuid4().hex[:6]}.local/api/{uuid.uuid4().hex[:6]}"
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        mock_response_data = {"status": "ok", "uuid": uuid.uuid4().hex}

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
            "score": self.score,
            "timestamp": self.timestamp
        }
        res = render_health_dashboard(metrics)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_normalization_and_valid(self):
        health_score = round(random.uniform(0.0, 100.0), 2)
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        input_data = {
            "health_score": health_score,
            "run_id": run_id
        }
        res = validate_repo_health_metrics(input_data)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], health_score)
        self.assertEqual(res["metrics"]["metric_name"], run_id)
        self.assertIn("timestamp", res["metrics"])

    def test_validate_repo_health_metrics_invalid(self):
        invalid_score = 200.0 + random.uniform(1.0, 100.0)
        input_data = {
            "health_score": invalid_score,
            "run_id": f"run_{uuid.uuid4().hex[:8]}"
        }
        res = validate_repo_health_metrics(input_data)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], invalid_score)


if __name__ == '__main__':
    unittest.main()