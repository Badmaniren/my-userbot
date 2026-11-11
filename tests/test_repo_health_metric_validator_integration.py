import unittest
import uuid
import random
import json
import io
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    validate_repo_health_metrics,
    audit_repository,
    render_health_dashboard
)


class TestRepoHealthMetricValidatorIntegration(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1700000000)

    def test_end_to_end_metric_pipeline_success(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "metadata": {
                "run_uuid": str(uuid.uuid4())
            }
        }

        stream_data = json.dumps(payload)
        stream = io.StringIO(stream_data)

        validated_stream_data = self.validator.validate_stream(stream)
        self.assertEqual(len(validated_stream_data), 1)
        self.assertEqual(validated_stream_data[0]["metric_name"], self.random_metric_name)

        wrapper_result = validate_repo_health_metrics(payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], self.random_score)

        audited_data = audit_repository(wrapper_result["metrics"])
        self.assertEqual(audited_data["timestamp"], self.random_timestamp)

        dashboard_output = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

    def test_normalization_and_validation_integration(self):
        alt_score = round(random.uniform(10.0, 90.0), 2)
        alt_run_id = f"run_{uuid.uuid4().hex[:6]}"

        raw_payload = {
            "health_score": alt_score,
            "run_id": alt_run_id
        }

        wrapper_result = validate_repo_health_metrics(raw_payload)

        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], alt_score)
        self.assertEqual(wrapper_result["metrics"]["metric_name"], alt_run_id)
        self.assertIn("timestamp", wrapper_result["metrics"])

        stream_bytes = json.dumps(wrapper_result["metrics"]).encode('utf-8')
        byte_stream = io.BytesIO(stream_bytes)

        stream_results = self.validator.validate_stream(byte_stream)
        self.assertEqual(stream_results[0]["score"], alt_score)
        self.assertEqual(stream_results[0]["metric_name"], alt_run_id)

    def test_validation_failure_propagation(self):
        invalid_score = random.choice([-50.0 - random.random(), 100.1 + random.random()])
        bad_payload = {
            "metric_name": f"err_{uuid.uuid4().hex[:4]}",
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        wrapper_result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], invalid_score)

        stream = io.StringIO(json.dumps(bad_payload))
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)


if __name__ == "__main__":
    unittest.main()