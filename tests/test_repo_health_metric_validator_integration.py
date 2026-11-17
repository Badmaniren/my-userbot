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
        self.metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.score = round(random.uniform(0.0, 100.0), 2)
        self.timestamp = f"2023-10-{random.randint(10, 28)}T12:00:00Z"
        
        self.valid_payload = {
            "metric_name": self.metric_name,
            "score": self.score,
            "timestamp": self.timestamp
        }

    def test_full_metric_lifecycle_and_dashboard_rendering(self):
        # 1. Validate through class method
        is_valid = self.validator.validate(self.valid_payload)
        self.assertTrue(is_valid)

        # 2. Audit repository integration step
        audited_data = audit_repository(self.valid_payload)
        self.assertEqual(audited_data["metric_name"], self.metric_name)
        self.assertEqual(audited_data["score"], self.score)

        # 3. Stream validation integration
        stream_data = json.dumps([self.valid_payload])
        validated_stream = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_stream), 1)
        self.assertEqual(validated_stream[0]["metric_name"], self.metric_name)

        # 4. Alternative keys normalization integration
        alt_payload = {
            "run_id": f"run_{uuid.uuid4().hex[:6]}",
            "health_score": self.score,
            "timestamp": self.timestamp
        }
        normalization_result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(normalization_result["is_valid"])
        self.assertEqual(normalization_result["metrics"]["metric_name"], alt_payload["run_id"])
        self.assertEqual(normalization_result["metrics"]["score"], self.score)

        # 5. Dashboard rendering integration
        dashboard_output = render_health_dashboard(normalization_result["metrics"])
        self.assertIn(alt_payload["run_id"], dashboard_output)
        self.assertIn(str(self.score), dashboard_output)

    def test_validation_failure_propagation(self):
        invalid_score = round(random.uniform(101.0, 200.0), 2)
        invalid_payload = {
            "metric_name": f"bad_metric_{uuid.uuid4().hex[:6]}",
            "score": invalid_score,
            "timestamp": self.timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_payload)

        normalization_result = validate_repo_health_metrics(invalid_payload)
        self.assertFalse(normalization_result["is_valid"])

if __name__ == "__main__":
    unittest.main()