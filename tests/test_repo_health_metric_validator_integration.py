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

    def test_full_metric_pipeline_integration(self):
        raw_payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "extra_meta": uuid.uuid4().hex
        }

        stream_data = json.dumps([raw_payload])
        validated_stream_results = self.validator.validate_stream(stream_data)
        
        self.assertEqual(len(validated_stream_results), 1)
        self.assertEqual(validated_stream_results[0]["metric_name"], self.random_metric_name)

        audit_result = audit_repository(validated_stream_results[0])
        self.assertEqual(audit_result["score"], self.random_score)

        dashboard_output = render_health_dashboard(audit_result)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

        wrapper_input = {
            "health_score": self.random_score,
            "run_id": self.random_metric_name
        }
        wrapper_result = validate_repo_health_metrics(wrapper_input)
        
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], self.random_score)
        self.assertEqual(wrapper_result["metrics"]["metric_name"], self.random_metric_name)

    def test_invalid_metric_rejection_flow(self):
        invalid_score = random.choice([-10.5, 105.0, 200.0])
        bad_payload = {
            "metric_name": f"bad_{uuid.uuid4().hex[:6]}",
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        wrapper_result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(wrapper_result["is_valid"])

if __name__ == "__main__":
    unittest.main()