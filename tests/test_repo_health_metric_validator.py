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
    validate_repo_health_metrics
)


class TestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.metric_name_rand = f"metric_{uuid.uuid4().hex[:8]}"
        self.score_rand = round(random.uniform(0.0, 100.0), 2)
        self.timestamp_rand = f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}"

    def test_validate_success(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        result = self.validator.validate(metric)
        self.assertTrue(result)

    def test_validate_not_dict_raises(self):
        invalid_metric = random.choice([
            f"string_{uuid.uuid4().hex[:6]}",
            random.randint(1, 1000),
            [random.randint(1, 100)]
        ])
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_metric)

    def test_validate_missing_required_field_raises(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_invalid_score_type_or_range_raises(self):
        bad_scores = [
            "".join(random.choices(string.ascii_letters, k=5)),
            -random.uniform(0.1, 50.0),
            100.1 + random.uniform(0.1, 50.0)
        ]
        for score in bad_scores:
            metric = {
                "metric_name": self.metric_name_rand,
                "score": score,
                "timestamp": self.timestamp_rand
            }
            with self.assertRaises(MetricValidationError):
                self.validator.validate(metric)

    def test_validate_stream_bytes_success(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        stream_bytes = json.dumps(metric).encode('utf-8')
        result = self.validator.validate_stream(stream_bytes)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name_rand)
        self.assertEqual(result[0]["score"], self.score_rand)

    def test_validate_stream_io_success(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        stream_io = io.StringIO(json.dumps(metric))
        result = self.validator.validate_stream(stream_io)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name_rand)

    def test_validate_stream_invalid_json_raises(self):
        bad_stream = io.BytesIO(f"invalid_json_{uuid.uuid4().hex}".encode('utf-8'))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_stream)

    def test_validate_stream_invalid_structure_raises(self):
        bad_array_stream = io.StringIO(json.dumps(random.randint(100, 999)))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(bad_array_stream)

    def test_dispatch_and_validate_remote_success(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        endpoint = f"https://{uuid.uuid4().hex[:8]}.com/api/v1/metrics"
        expected_response = {"status": "success", "id": uuid.uuid4().hex}

        with patch('requests.post') as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            response_data = self.validator.dispatch_and_validate_remote(metric, endpoint)
            
            mock_post.assert_called_once_with(endpoint, json=metric)
            self.assertEqual(response_data, expected_response)

    def test_audit_repository_success(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        result = audit_repository(metric)
        self.assertEqual(result, metric)

    def test_render_health_dashboard_contains_metrics(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        dashboard_str = render_health_dashboard(metric)
        self.assertIn(self.metric_name_rand, dashboard_str)
        self.assertIn(str(self.score_rand), dashboard_str)

    def test_validate_repo_health_metrics_valid_payload(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        result = validate_repo_health_metrics(metric)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], self.metric_name_rand)

    def test_validate_repo_health_metrics_aliased_fields(self):
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        health_score = round(random.uniform(0.0, 100.0), 2)
        timestamp = self.timestamp_rand

        payload = {
            "run_id": run_id,
            "health_score": health_score,
            "timestamp": timestamp
        }
        result = validate_repo_health_metrics(payload)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], run_id)
        self.assertEqual(result["metrics"]["score"], health_score)

    def test_validate_repo_health_metrics_invalid_payload(self):
        payload = {
            "metric_name": self.metric_name_rand,
            "score": f"bad_score_{uuid.uuid4().hex[:4]}",
            "timestamp": self.timestamp_rand
        }
        result = validate_repo_health_metrics(payload)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"], payload)

    def test_validate_repo_health_metrics_not_a_dict(self):
        payload = [random.randint(1, 100), uuid.uuid4().hex]
        result = validate_repo_health_metrics(payload)
        self.assertFalse(result["is_valid"])
        self.assertEqual(result["metrics"], payload)