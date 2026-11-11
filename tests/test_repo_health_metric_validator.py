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

    def test_validate_success_random_data(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1000000000, 2000000000)

        payload = {
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp,
            "extra_field": uuid.uuid4().hex
        }

        result = self.validator.validate(payload)
        self.assertTrue(result)

    def test_validate_invalid_not_dict(self):
        invalid_data = [uuid.uuid4().hex, random.randint(1, 100)]
        for item in invalid_data:
            with self.assertRaises(MetricValidationError):
                self.validator.validate(item)

    def test_validate_missing_mandatory_fields(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1000000000, 2000000000)

        missing_name = {"score": score, "timestamp": timestamp}
        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_name)

        missing_score = {"metric_name": metric_name, "timestamp": timestamp}
        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_score)

        missing_timestamp = {"metric_name": metric_name, "score": score}
        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_timestamp)

    def test_validate_invalid_score_types_and_bounds(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        timestamp = random.randint(1000000000, 2000000000)

        invalid_types = [uuid.uuid4().hex, True, False, None, [1, 2], {"nested": 1}]
        for bad_score in invalid_types:
            payload = {"metric_name": metric_name, "score": bad_score, "timestamp": timestamp}
            with self.assertRaises(MetricValidationError):
                self.validator.validate(payload)

        out_of_bounds = [-random.uniform(0.1, 1000.0), 100.0 + random.uniform(0.1, 1000.0)]
        for bad_score in out_of_bounds:
            payload = {"metric_name": metric_name, "score": bad_score, "timestamp": timestamp}
            with self.assertRaises(MetricValidationError):
                self.validator.validate(payload)

    def test_validate_stream_bytes_and_string(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        score = round(random.uniform(0.0, 100.0), 2)
        timestamp = random.randint(1000000000, 2000000000)

        metric_dict = {
            "metric_name": metric_name,
            "score": score,
            "timestamp": timestamp
        }

        json_str = json.dumps(metric_dict)
        stream_str = io.StringIO(json_str)

        result_str = self.validator.validate_stream(stream_str)
        self.assertEqual(len(result_str), 1)
        self.assertEqual(result_str[0]["metric_name"], metric_name)
        self.assertEqual(result_str[0]["score"], score)

        stream_bytes = io.BytesIO(json_str.encode('utf-8'))
        result_bytes = self.validator.validate_stream(stream_bytes)
        self.assertEqual(len(result_bytes), 1)
        self.assertEqual(result_bytes[0]["metric_name"], metric_name)

    def test_validate_stream_decode_error(self):
        bad_bytes = io.BytesIO(b'\xff\xfe\xfd_invalid_utf8_bytes_' + uuid.uuid4().bytes)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_bytes)

    def test_validate_stream_json_decode_error(self):
        corrupt_json = f"{{invalid_json_key: {uuid.uuid4().hex}}}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(corrupt_json)

    def test_dispatch_and_validate_remote(self):
        endpoint_url = f"https://{uuid.uuid4().hex}.example.com/api/v1/metrics"
        payload = {
            "metric_name": f"metric_{uuid.uuid4().hex[:8]}",
            "score": round(random.uniform(0.0, 100.0), 2),
            "timestamp": random.randint(1000000000, 2000000000)
        }
        expected_response = {"status": uuid.uuid4().hex, "acknowledged": True}

        with patch("requests.post") as mock_post:
            mock_resp = MagicMock()
            mock_resp.json.return_value = expected_response
            mock_post.return_value = mock_resp

            resp_data = self.validator.dispatch_and_validate_remote(payload, endpoint_url)

            mock_post.assert_called_once_with(endpoint_url, json=payload)
            self.assertEqual(resp_data, expected_response)

    def test_audit_repository_wrapper(self):
        payload = {
            "metric_name": f"metric_{uuid.uuid4().hex[:8]}",
            "score": round(random.uniform(0.0, 100.0), 2),
            "timestamp": random.randint(1000000000, 2000000000),
            "random_token": uuid.uuid4().hex
        }
        res = audit_repository(payload)
        self.assertEqual(res, payload)

    def test_render_health_dashboard(self):
        payload = {
            f"key_{uuid.uuid4().hex[:4]}": uuid.uuid4().hex
        }
        res = render_health_dashboard(payload)
        self.assertIsInstance(res, str)
        self.assertTrue(len(res) > 0)

    def test_validate_repo_health_metrics_normalization_and_wrapper(self):
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        health_score = round(random.uniform(0.0, 100.0), 2)

        input_data = {
            "run_id": run_id,
            "health_score": health_score
        }

        result = validate_repo_health_metrics(input_data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], health_score)
        self.assertEqual(result["metrics"]["timestamp"], 1600000000)

    def test_validate_repo_health_metrics_invalid_case(self):
        run_id = f"run_{uuid.uuid4().hex[:8]}"
        bad_score = random.choice([-50.0, 150.0, ''.join(random.choices(string.ascii_letters, k=5))])

        input_data = {
            "run_id": run_id,
            "health_score": bad_score
        }

        result = validate_repo_health_metrics(input_data)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], bad_score)


if __name__ == "__main__":
    unittest.main()