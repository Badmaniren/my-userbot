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
        valid_data = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        result = self.validator.validate(valid_data)
        self.assertTrue(result)

    def test_validate_not_a_dict(self):
        invalid_data = f"not_a_dict_{uuid.uuid4().hex}"
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

    def test_validate_invalid_score_type_bool(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "score": True,
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_invalid_score_type_string(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "score": f"{uuid.uuid4().hex[:4]}",
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds_low(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "score": -random.uniform(0.1, 50.0),
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_score_out_of_bounds_high(self):
        invalid_data = {
            "metric_name": self.metric_name,
            "score": 100.0 + random.uniform(0.1, 50.0),
            "timestamp": self.timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_data)

    def test_validate_stream_bytes(self):
        item = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        payload = json.dumps(item).encode('utf-8')
        stream = io.BytesIO(payload)
        
        results = self.validator.validate_stream(stream)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["metric_name"], self.metric_name)

    def test_validate_stream_string(self):
        item = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        payload = json.dumps(item)
        
        results = self.validator.validate_stream(payload)
        self.assertEqual(len(results), 1)
        self.assertEqual(results[0]["score"], self.score)

    def test_validate_stream_list(self):
        items = [
            {
                "metric_name": f"{self.metric_name}_1",
                "score": self.score,
                "timestamp": self.timestamp
            },
            {
                "metric_name": f"{self.metric_name}_2",
                "score": self.score,
                "timestamp": self.timestamp
            }
        ]
        payload = json.dumps(items)
        
        results = self.validator.validate_stream(payload)
        self.assertEqual(len(results), 2)
        self.assertEqual(results[0]["metric_name"], items[0]["metric_name"])
        self.assertEqual(results[1]["metric_name"], items[1]["metric_name"])

    def test_validate_stream_invalid_bytes_decode(self):
        bad_stream = io.BytesIO(b'\xff\xfe\xfd')
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_stream)

    def test_validate_stream_invalid_json(self):
        bad_json = f"not_json_{uuid.uuid4().hex}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_json)

    def test_dispatch_and_validate_remote(self):
        endpoint = f"https://api.{uuid.uuid4().hex}.local/v1/metrics"
        payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        expected_response = {"status": "ok", "uuid": uuid.uuid4().hex}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            result = self.validator.dispatch_and_validate_remote(payload, endpoint)
            
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(result, expected_response)

    def test_audit_repository(self):
        data = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        res = audit_repository(data)
        self.assertEqual(res, data)

    def test_render_health_dashboard(self):
        data = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }
        res = render_health_dashboard(data)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_valid_normalized(self):
        raw_data = {
            "health_score": self.score,
            "run_id": self.metric_name
        }
        res = validate_repo_health_metrics(raw_data)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], self.score)
        self.assertEqual(res["metrics"]["metric_name"], self.metric_name)
        self.assertIn("timestamp", res["metrics"])

    def test_validate_repo_health_metrics_invalid(self):
        raw_data = {
            "health_score": -10.0,
            "run_id": self.metric_name
        }
        res = validate_repo_health_metrics(raw_data)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], -10.0)


if __name__ == "__main__":
    unittest.main()