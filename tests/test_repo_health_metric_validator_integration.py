import unittest
import json
import uuid
import random
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics
)


class IntegrationTestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = f"metric_{uuid.uuid4().hex}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_full_metric_validation_and_pipeline_integration(self):
        raw_payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "extra_metadata": {
                "session_uuid": uuid.uuid4().str
            }
        }

        stream_data = json.dumps([raw_payload])
        validated_stream_result = self.validator.validate_stream(stream_data)

        self.assertEqual(len(validated_stream_result), 1)
        self.assertEqual(validated_stream_result[0]["metric_name"], self.random_metric_name)
        self.assertEqual(validated_stream_result[0]["score"], self.random_score)

        audit_result = audit_repository(validated_stream_result[0])
        self.assertIn("metric_name", audit_result)
        self.assertEqual(audit_result["score"], self.random_score)

        dashboard_output = render_health_dashboard(audit_result)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

    def test_integration_wrapper_normalization_and_validation(self):
        alt_metric_name = f"run_{uuid.uuid4().hex[:8]}"
        alt_score = round(random.uniform(10.0, 90.0), 2)

        unnormalized_data = {
            "run_id": alt_metric_name,
            "health_score": alt_score
        }

        wrapped_result = validate_repo_health_metrics(unnormalized_data)

        self.assertTrue(wrapped_result["is_valid"])
        self.assertEqual(wrapped_result["metrics"]["metric_name"], alt_metric_name)
        self.assertEqual(wrapped_result["metrics"]["score"], alt_score)
        self.assertIn("timestamp", wrapped_result["metrics"])

    def test_invalid_metric_rejection_pipeline(self):
        invalid_score = random.choice([-15.5, 105.0, 200.0])
        bad_payload = {
            "metric_name": f"fail_metric_{uuid.uuid4().hex}",
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        wrapped_result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(wrapped_result["is_valid"])
        self.assertEqual(wrapped_result["metrics"]["score"], invalid_score)


if __name__ == "__main__":
    unittest.main()