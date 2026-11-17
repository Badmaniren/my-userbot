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
        self.random_timestamp = int(random.randint(1600000000, 1700000000))

    def test_end_to_end_metric_lifecycle(self):
        payload = {
            "run_id": self.random_metric_name,
            "health_score": self.random_score,
            "timestamp": self.random_timestamp
        }

        validation_result = validate_repo_health_metrics(payload)
        self.assertTrue(validation_result["is_valid"])
        
        normalized_metric = validation_result["metrics"]
        self.assertEqual(normalized_metric["metric_name"], self.random_metric_name)
        self.assertEqual(normalized_metric["score"], self.random_score)

        audited_metric = audit_repository(normalized_metric)
        self.assertEqual(audited_metric, normalized_metric)

        dashboard_output = render_health_dashboard(audited_metric)
        self.assertIn(self.random_metric_name, dashboard_output)
        self.assertIn(str(self.random_score), dashboard_output)

        stream_data = json.dumps([normalized_metric])
        validated_stream = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_stream), 1)
        self.assertEqual(validated_stream[0]["metric_name"], self.random_metric_name)

    def test_invalid_metric_handling(self):
        bad_score = round(random.uniform(101.0, 200.0), 2)
        payload = {
            "metric_name": f"err_{uuid.uuid4().hex[:6]}",
            "score": bad_score,
            "timestamp": self.random_timestamp
        }

        validation_result = validate_repo_health_metrics(payload)
        self.assertFalse(validation_result["is_valid"])

        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload)

if __name__ == "__main__":
    unittest.main()