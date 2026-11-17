import unittest
import uuid
import random
import json
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics
)

class TestRepoHealthMetricValidatorIntegration(unittest.TestCase):
    
    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_end_to_end_metric_lifecycle(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        audit_result = audit_repository(payload)
        self.assertEqual(audit_result["metric_name"], self.random_metric_name)
        self.assertEqual(audit_result["score"], self.random_score)

        dashboard_output = render_health_dashboard(payload)
        self.assertIn(self.random_metric_name, dashboard_output)
        self.assertIn(str(self.random_score), dashboard_output)

        stream_data = json.dumps([payload])
        validated_stream = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_stream), 1)
        self.assertEqual(validated_stream[0]["metric_name"], self.random_metric_name)

    def test_alternative_format_normalization_pipeline(self):
        alt_payload = {
            "run_id": f"run_{uuid.uuid4().hex[:6]}",
            "health_score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": self.random_timestamp
        }

        result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], alt_payload["run_id"])
        self.assertEqual(result["metrics"]["score"], alt_payload["health_score"])

    def test_metric_validation_bounds_failure(self):
        bad_score = 105.5
        payload = {
            "metric_name": self.random_metric_name,
            "score": bad_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

        alt_payload = {
            "metric_name": self.random_metric_name,
            "health_score": bad_score,
            "timestamp": self.random_timestamp
        }

        normalization_result = validate_repo_health_metrics(alt_payload)
        self.assertFalse(normalization_result["is_valid"])
        self.assertEqual(normalization_result["metrics"]["score"], bad_score)

if __name__ == "__main__":
    unittest.main()