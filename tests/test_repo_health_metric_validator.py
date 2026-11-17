import unittest
from unittest.mock import patch, MagicMock
import json
import io
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
        self.metric_name_rand = f"metric_{uuid.uuid4().hex[:8]}"
        self.score_rand = round(random.uniform(0.0, 100.0), 2)
        self.timestamp_rand = f"2023-{random.randint(1,12):02d}-{random.randint(1,28):02d}T{random.randint(0,23):02d}:{random.randint(0,59):02d}:{random.randint(0,59):02d}Z"

    def test_validate_success(self):
        valid_metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        result = self.validator.validate(valid_metric)
        self.assertTrue(result)

    def test_validate_not_a_dictionary(self):
        invalid_metric = random.choice([
            f"string_{uuid.uuid4().hex}",
            random.randint(1, 1000),
            [uuid.uuid4().hex, uuid.uuid4().hex],
            None
        ])
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_metric)

    def test_validate_missing_required_fields(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_invalid_score_type(self):
        metric = {
            "metric_name": self.metric_name_rand,
            "score": f"{uuid.uuid4().hex}",
            "timestamp": self.timestamp_rand
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_score_out_of_range(self):
        out_of_bounds = random.choice([
            round(random.uniform(-1000.0, -0.01), 2),
            round(random.uniform(100.01, 1000.0), 2)
        ])
        metric = {
            "metric_name": self.metric_name_rand,
            "score": out_of_bounds,
            "timestamp": self.timestamp_rand
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(metric)

    def test_validate_stream_json_array(self):
        metric_list = [
            {
                "metric_name": f"{self.metric_name_rand}_1",
                "score": self.score_rand,
                "timestamp": self.timestamp_rand
            },
            {
                "metric_name": f"{self.metric_name_rand}_2",
                "score": round(self.score_rand / 2, 2),
                "timestamp": self.timestamp_rand
            }
        ]
        stream_data = json.dumps(metric_list)
        stream = io.BytesIO(stream_data.encode('utf-8'))
        
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["metric_name"], metric_list[0]["metric_name"])

    def test_validate_stream_json_object(self):
        metric_obj = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        stream_data = json.dumps(metric_obj)
        stream = io.StringIO(stream_data)

        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name_rand)

    def test_validate_stream_invalid_format(self):
        corrupted_data = f"{{invalid_json_{uuid.uuid4().hex}"
        stream = io.BytesIO(corrupted_data.encode('utf-8'))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)

    def test_dispatch_and_validate_remote(self):
        valid_metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        endpoint_url = f"https://{uuid.uuid4().hex}.com/api/v1/metrics"
        expected_response = {"status": uuid.uuid4().hex, "received": True}

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            response = self.validator.dispatch_and_validate_remote(valid_metric, endpoint_url)
            
            mock_post.assert_called_once_with(endpoint_url, json=valid_metric)
            self.assertEqual(response, expected_response)

    def test_audit_repository(self):
        valid_metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        audited = audit_repository(valid_metric)
        self.assertEqual(audited, valid_metric)

    def test_render_health_dashboard(self):
        valid_metric = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        dashboard_str = render_health_dashboard(valid_metric)
        self.assertIn(self.metric_name_rand, dashboard_str)
        self.assertIn(str(self.score_rand), dashboard_str)

    def test_render_health_dashboard_fallback(self):
        empty_metric = {}
        dashboard_str = render_health_dashboard(empty_metric)
        self.assertIn("Unknown", dashboard_str)
        self.assertIn("0.0", dashboard_str)

    def test_validate_repo_health_metrics_success(self):
        payload = {
            "metric_name": self.metric_name_rand,
            "score": self.score_rand,
            "timestamp": self.timestamp_rand
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], self.metric_name_rand)

    def test_validate_repo_health_metrics_aliases_transformation(self):
        run_id_val = f"run_{uuid.uuid4().hex[:6]}"
        health_score_val = round(random.uniform(10.0, 90.0), 2)
        
        payload = {
            "run_id": run_id_val,
            "health_score": health_score_val,
            "timestamp": self.timestamp_rand
        }
        res = validate_repo_health_metrics(payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], run_id_val)
        self.assertEqual(res["metrics"]["score"], health_score_val)

    def test_validate_repo_health_metrics_invalid(self):
        payload = {
            "metric_name": self.metric_name_rand,
            "score": f"invalid_{uuid.uuid4().hex}",
            "timestamp": self.timestamp_rand
        }
        res = validate_repo_health_metrics(payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"], payload)


if __name__ == "__main__":
    unittest.main()