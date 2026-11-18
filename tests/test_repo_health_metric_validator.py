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
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.timestamp = f"2023-10-{random.randint(10, 28)}T{random.randint(0, 23)}:{random.randint(0, 59)}:00Z"
        self.score = round(random.uniform(0.0, 100.0), 2)
        self.valid_metric = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }

    def test_validate_success(self):
        result = self.validator.validate(self.valid_metric)
        self.assertTrue(result)

    def test_validate_not_a_dictionary(self):
        invalid_metric = [random.randint(1, 100), uuid.uuid4().hex]
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_metric)

    def test_validate_missing_required_fields(self):
        for field in ["metric_name", "score", "timestamp"]:
            broken_metric = self.valid_metric.copy()
            del broken_metric[field]
            with self.assertRaises(MetricValidationError):
                self.validator.validate(broken_metric)

    def test_validate_invalid_score_types_and_ranges(self):
        invalid_scores = [
            uuid.uuid4().hex,
            None,
            random.uniform(-100.0, -0.01),
            random.uniform(100.01, 200.0)
        ]
        for bad_score in invalid_scores:
            broken_metric = self.valid_metric.copy()
            broken_metric["score"] = bad_score
            with self.assertRaises(MetricValidationError):
                self.validator.validate(broken_metric)

    def test_validate_stream_with_bytes(self):
        stream_data = json.dumps([self.valid_metric]).encode('utf-8')
        stream = io.BytesIO(stream_data)
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)
        self.assertEqual(result[0]["score"], self.score)

    def test_validate_stream_with_string_io(self):
        stream_data = json.dumps(self.valid_metric)
        stream = io.StringIO(stream_data)
        result = self.validator.validate_stream(stream)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["metric_name"], self.metric_name)

    def test_validate_stream_with_raw_bytes(self):
        raw_bytes = json.dumps([self.valid_metric]).encode('utf-8')
        result = self.validator.validate_stream(raw_bytes)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["timestamp"], self.timestamp)

    def test_validate_stream_invalid_json(self):
        invalid_content = io.BytesIO(b"{ malformed_json")
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(invalid_content)

    def test_validate_stream_invalid_root_structure(self):
        scalar_content = io.BytesIO(json.dumps(random.randint(1, 500)).encode('utf-8'))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(scalar_content)

    def test_dispatch_and_validate_remote(self):
        endpoint_url = f"https://{uuid.uuid4().hex}.com/api/v1/metrics"
        expected_response = {"status": uuid.uuid4().hex, "processed": True}

        with patch("requests.post") as mock_post:
            mock_response = MagicMock()
            mock_response.json.return_value = expected_response
            mock_post.return_value = mock_response

            response = self.validator.dispatch_and_validate_remote(self.valid_metric, endpoint_url)
            
            mock_post.assert_called_once_with(endpoint_url, json=self.valid_metric)
            self.assertEqual(response, expected_response)

    def test_audit_repository(self):
        audited = audit_repository(self.valid_metric)
        self.assertEqual(audited, self.valid_metric)

    def test_audit_repository_invalid_raises(self):
        broken_metric = self.valid_metric.copy()
        del broken_metric["score"]
        with self.assertRaises(MetricValidationError):
            audit_repository(broken_metric)

    def test_render_health_dashboard(self):
        dashboard_str = render_health_dashboard(self.valid_metric)
        self.assertIn(self.metric_name, dashboard_str)
        self.assertIn(str(self.score), dashboard_str)

    def test_render_health_dashboard_missing_fields(self):
        empty_metric = {}
        dashboard_str = render_health_dashboard(empty_metric)
        self.assertIn("Unknown", dashboard_str)
        self.assertIn("0.0", dashboard_str)

    def test_validate_repo_health_metrics_success_direct(self):
        res = validate_repo_health_metrics(self.valid_metric)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], self.metric_name)

    def test_validate_repo_health_metrics_normalization(self):
        run_id = f"run_{uuid.uuid4().hex[:6]}"
        health_score = round(random.uniform(10.0, 90.0), 2)
        timestamp = f"2023-11-{random.randint(10, 20)}T00:00:00Z"
        
        raw_payload = {
            "run_id": run_id,
            "health_score": health_score,
            "timestamp": timestamp
        }

        res = validate_repo_health_metrics(raw_payload)
        self.assertTrue(res["is_valid"])
        self.assertEqual(res["metrics"]["metric_name"], run_id)
        self.assertEqual(res["metrics"]["score"], health_score)

    def test_validate_repo_health_metrics_failure_payload(self):
        bad_payload = [uuid.uuid4().hex, random.randint(1, 100)]
        res = validate_repo_health_metrics(bad_payload)
        self.assertFalse(res["is_valid"])
        self.assertEqual(res["metrics"], bad_payload)


if __name__ == '__main__':
    unittest.main()