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

    def test_validate_not_a_dict_raises(self):
        invalid_data = [self.metric_name, self.score, self.timestamp]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_metric_name_raises(self):
        invalid_data = {
            "score": self.score,
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_score_raises(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_missing_timestamp_raises(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "score": self.score
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_invalid_score_type_raises(self):
        for bad_score in [f"str_{uuid.uuid4().hex[:4]}", True, False, None, {}]:
            invalid_data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds_raises(self):
        for bad_score in [-random.uniform(0.1, 100.0), 100.1 + random.uniform(0.0, 50.0)]:
            invalid_data = {
                "metric_name": self.metric_name,
                "score": bad_score,
                "timestamp": self.timestamp
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(invalid_data)

    def test_validate_stream_bytes_success(self):
        payload = [{
            "metric_name": f"stream_metric_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": random.randint(1600000000, 1700000000)
        }]
        stream = io.BytesIO(json.dumps(payload).encode('utf-8'))
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], payload[0]["metric_name"])

    def test_validate_stream_string_success(self):
        payload = {
            "metric_name": f"str_metric_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": random.randint(1600000000, 1700000000)
        }
        stream_str = json.dumps(payload)
        result = self.validator.validate_stream(stream_str)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], payload["score"])

    def test_validate_stream_invalid_json_raises(self):
        bad_stream = io.BytesIO(f"invalid_json_{uuid.uuid4().hex}".encode('utf-8'))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_stream)

    def test_validate_stream_undecodable_bytes_raises(self):
        bad_bytes = b'\xff\xfe\xfd\xfc'
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_bytes)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://{uuid.uuid4().hex}.example.com/api/v1/metrics"
        payload = {
            "metric_name": f"remote_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(0.0, 100.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        mock_response_data = {"status": "success", "received_id": uuid.uuid4().hex}

        with patch("skills.repo_health_metric_validator.requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            resp = self.validator.dispatch_and_validate_remote(payload, endpoint)
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(resp, mock_response_data)

    def test_audit_repository(self):
        data = {
            "metric_name": f"audit_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(0.0, 100.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        res = audit_repository(data)
        self.assertEqual(res, data)

    def test_render_health_dashboard(self):
        data = {
            "metric_name": f"dash_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(0.0, 100.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        res = render_health_dashboard(data)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_valid(self):
        data = {
            "metric_name": f"health_{uuid.uuid4().hex[:6]}",
            "score": round(random.uniform(20.0, 80.0), 2),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        res = validate_repo_health_metrics(data)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], data["metric_name"])

    def test_validate_repo_health_metrics_normalization(self):
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        health_score = round(random.uniform(40.0, 95.0), 2)
        data = {
            "run_id": run_id,
            "health_score": health_score
        }
        res = validate_repo_health_metrics(data)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], run_id)
        self.assertEqual(res["metrics"]["score"], health_score)
        self.assertIn("timestamp", res["metrics"])

    def test_validate_repo_health_metrics_invalid(self):
        data = {
            "metric_name": f"broken_{uuid.uuid4().hex[:6]}",
            "score": random.uniform(105.0, 200.0),
            "timestamp": random.randint(1500000000, 1800000000)
        }
        res = validate_repo_health_metrics(data)
        self.assertFalse(res["is_valid"])


if __name__ == '__main__':
    unittest.main()