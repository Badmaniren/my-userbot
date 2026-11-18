import unittest
from unittest.mock import patch, MagicMock
import json
import io
import uuid
import random
import string
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
        self.metric_name_seed = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1600000000, 1750000000)

    def test_validate_success(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        self.assertTrue(self.validator.validate(metric))

    def test_validate_not_a_dict(self):
        invalid_metric = random.choice([
            f"string_{uuid.uuid4().hex}",
            random.randint(1, 100),
            [uuid.uuid4().hex, uuid.uuid4().hex]
        ])
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_metric)

    def test_validate_missing_required_fields(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_invalid_score_type(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": f"{uuid.uuid4().hex[:4]}",
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_invalid_score_range_too_high(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": 100.1 + random.uniform(1.0, 50.0),
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_invalid_score_range_too_low(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": -0.1 - random.uniform(1.0, 50.0),
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_stream_bytes(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        payload_bytes = json.dumps(metric).encode('utf-8')
        result = self.validator.validate_stream(payload_bytes)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name_seed)

    def test_validate_stream_io_bytes(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        stream = io.BytesIO(json.dumps(metric).encode('utf-8'))
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["score"], self.random_score)

    def test_validate_stream_json_array(self):
        metrics = [
            {
                "metric_name": f"{self.metric_name_seed}_1",
                "score": self.random_score,
                "timestamp": self.random_timestamp
            },
            {
                "metric_name": f"{self.metric_name_seed}_2",
                "score": self.random_score,
                "timestamp": self.random_timestamp
            }
        ]
        stream = json.dumps(metrics)
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["metric_name"], metrics[0]["metric_name"])
        self.assertEqual(result[1]["metric_name"], metrics[1]["metric_name"])

    def test_validate_stream_invalid_json(self):
        bad_content = f"{{invalid_json_{uuid.uuid4().hex}}}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_content)

    def test_validate_stream_invalid_structure(self):
        bad_structure = json.dumps(random.randint(1, 500))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_structure)

    def test_dispatch_and_validate_remote(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        endpoint = f"https://{uuid.uuid4().hex}.internal/api/metrics"
        expected_response = {"status": "success", "token": uuid.uuid4().hex}

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            res = self.validator.dispatch_and_validate_remote(metric, endpoint)
            self.assertEqual(res, expected_response)
            mock_post.assert_called_once_with(endpoint, json=metric)

    def test_audit_repository(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        res = audit_repository(metric)
        self.assertEqual(res, metric)

    def test_render_health_dashboard(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        dashboard_str = render_health_dashboard(metric)
        self.assertIn(self.metric_name_seed, dashboard_str)
        self.assertIn(str(self.random_score), dashboard_str)

    def test_render_health_dashboard_defaults(self):
        metric = {}
        dashboard_str = render_health_dashboard(metric)
        self.assertIn("Unknown", dashboard_str)
        self.assertIn("0.0", dashboard_str)

    def test_validate_repo_health_metrics_valid_direct(self):
        metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        res = validate_repo_health_metrics(metric)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], self.metric_name_seed)

    def test_validate_repo_health_metrics_aliases_transformation(self):
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        health_score = round(random.uniform(10.0, 90.0), 2)
        payload = {
            "run_id": run_id,
            "health_score": health_score,
            "timestamp": self.random_timestamp
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], run_id)
        self.assertEqual(res["metrics"]["score"], health_score)

    def test_validate_repo_health_metrics_invalid_payload_type(self):
        non_dict_payload = f"payload_{uuid.uuid4().hex}"
        res = validate_repo_health_metrics(non_dict_payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"], non_dict_payload)

    def test_validate_repo_health_metrics_unrecoverable_failure(self):
        bad_payload = {
            "random_field": uuid.uuid4().hex
        }
        res = validate_repo_health_metrics(bad_payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"], bad_payload)