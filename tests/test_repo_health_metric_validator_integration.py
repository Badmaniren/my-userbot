import unittest
import uuid
import random
import io
import json
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
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_end_to_end_metric_pipeline(self):
        raw_payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        json_bytes = json.dumps(raw_payload).encode('utf-8')
        stream = io.BytesIO(json_bytes)

        validated_list = self.validator.validate_stream(stream)
        self.assertEqual(len(validated_list), 1)
        self.assertEqual(validated_list[0]["metric_name"], self.random_metric_name)
        self.assertEqual(validated_list[0]["score"], self.random_score)

        integration_result = validate_repo_health_metrics(raw_payload)
        self.assertTrue(integration_result["is_valid"])
        self.assertEqual(integration_result["metrics"]["score"], self.random_score)

        audited_data = audit_repository(integration_result["metrics"])
        self.assertEqual(audited_data["metric_name"], self.random_metric_name)

        dashboard_output = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

    def test_normalization_and_strict_validation(self):
        alternative_payload = {
            "run_id": f"run_{uuid.uuid4().hex[:6]}",
            "health_score": round(random.uniform(10.0, 90.0), 2)
        }

        result = validate_repo_health_metrics(alternative_payload)
        self.assertTrue(result["is_valid"])
        self.assertIn("score", result["metrics"])

        invalid_payload = {
            "metric_name": self.random_metric_name,
            "score": 150.5,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_payload)

        invalid_stream = io.StringIO("Not a JSON")
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(invalid_stream)

if __name__ == "__main__":
    unittest.main()