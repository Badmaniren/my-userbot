import unittest
import uuid
import random
import json
import io
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

    def test_end_to_end_metric_flow_and_validation(self):
        raw_payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        stream_data = json.dumps([raw_payload])
        stream = io.StringIO(stream_data)

        validated_list = self.validator.validate_stream(stream)
        self.assertEqual(len(validated_list), 1)
        self.assertEqual(validated_list[0]["metric_name"], self.random_metric_name)
        self.assertEqual(validated_list[0]["score"], self.random_score)

        audit_result = audit_repository(validated_list[0])
        self.assertEqual(audit_result["metric_name"], self.random_metric_name)

        dashboard_output = render_health_dashboard(audit_result)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

        integration_result = validate_repo_health_metrics({
            "health_score": self.random_score,
            "run_id": self.random_metric_name
        })

        self.assertTrue(integration_result["is_valid"])
        self.assertEqual(integration_result["metrics"]["score"], self.random_score)
        self.assertEqual(integration_result["metrics"]["metric_name"], self.random_metric_name)
        self.assertIn("timestamp", integration_result["metrics"])

    def test_metric_validation_failure_boundaries(self):
        invalid_score = random.choice([-10.0, 105.5, "not_a_number", True])
        bad_payload = {
            "metric_name": f"bad_{uuid.uuid4().hex[:4]}",
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        integration_result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(integration_result["is_valid"])

if __name__ == "__main__":
    unittest.main()