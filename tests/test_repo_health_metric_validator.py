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
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_validate_success(self):
        valid_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(valid_data)
        self.assertTrue(result)

    def test_validate_not_dict(self):
        invalid_data = [uuid.uuid4().hex, self.random_score]
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
            corrupted_data = base_data.copy()
            del corrupted_data[field]
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(corrupted_data)
            self.assertIn(f"Missing mandatory field: '{field}'", str(ctx.exception))

    def test_validate_invalid_score_types(self):
        invalid_scores = [uuid.uuid4().hex, True, False, None, [self.random_score]]
        for bad_score in invalid_scores:
            data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(data)
            self.assertIn("Score must be a number", str(ctx.exception))

    def test_validate_score_out_of_bounds(self):
        out_of_bounds = [
            round(random.uniform(-100.0, -0.01), 2),
            round(random.uniform(100.01, 200.0), 2)
        ]
        for bad_score in out_of_bounds:
            data = {
                "metric_name": self.random_metric_name,
                "score": bad_score,
                "timestamp": self.random_timestamp
            }
            with self.assertRaises(MetricValidationError) as ctx:
                self.validator.validate(data)
            self.assertIn("score is out of bounds", str(ctx.exception))

    def test_validate_stream_valid_json_string(self):
        metric_item = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        stream_content = json.dumps(metric_item)
        validated = self.validator.validate_stream(stream_content)
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["metric_name"], self.random_metric_name)

    def test_validate_stream_valid_bytes(self):
        metric_item = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        stream_content = json.dumps(metric_item).encode('utf-8')
        validated = self.validator.validate_stream(stream_content)
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["score"], self.random_score)

    def test_validate_stream_io_object(self):
        metric_item = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        stream_io = io.BytesIO(json.dumps(metric_item).encode('utf-8'))
        validated = self.validator.validate_stream(stream_io)
        self.assertEqual(len(validated), 1)
        self.assertEqual(validated[0]["timestamp"], self.random_timestamp)

    def test_validate_stream_decode_error(self):
        bad_bytes = b'\xff\xfe\xfd'
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(bad_bytes)
        self.assertIn("Failed to decode stream bytes", str(ctx.exception))

    def test_validate_stream_json_decode_error(self):
        bad_json = f"not-a-json-{uuid.uuid4().hex}"
        with self.assertRaises(MetricValidationError) as ctx:
            self.validator.validate_stream(bad_json)
        self.assertIn("Failed to parse JSON", str(ctx.exception))

    def test_dispatch_and_validate_remote(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        endpoint = f"https://{uuid.uuid4().hex}.test/api/metrics"
        mock_response_data = {"status": uuid.uuid4().hex, "processed": True}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_response_data
            mock_post.return_value = mock_resp

            response = self.validator.dispatch_and_validate_remote(payload, endpoint)
            mock_post.assert_called_once_with(endpoint, json=payload)
            self.assertEqual(response, mock_response_data)

    def test_audit_repository(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = audit_repository(payload)
        self.assertEqual(result, payload)

    def test_render_health_dashboard(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = render_health_dashboard(payload)
        self.assertEqual(result, "dashboard_output.html")

    def test_validate_repo_health_metrics_normalization_valid(self):
        raw_data = {
            "health_score": self.random_score,
            "run_id": self.random_metric_name
        }
        res = validate_repo_health_metrics(raw_data)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], self.random_score)
        self.assertEqual(res["metrics"]["metric_name"], self.random_metric_name)
        self.assertEqual(res["metrics"]["timestamp"], 1600000000)

    def test_validate_repo_health_metrics_normalization_invalid(self):
        bad_score = round(random.uniform(105.0, 500.0), 2)
        raw_data = {
            "health_score": bad_score,
            "run_id": self.random_metric_name
        }
        res = validate_repo_health_metrics(raw_data)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"]["score"], bad_score)


if __name__ == "__main__":
    unittest.main()