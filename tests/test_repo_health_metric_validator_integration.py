import unittest
import uuid
import random
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

    def test_full_metric_lifecycle_and_pipeline_integration(self):
        raw_payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "extra_metadata": uuid.uuid4().hex
        }

        stream_data = json.dumps(raw_payload)
        
        validated_stream_items = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_stream_items), 1)
        self.assertEqual(validated_stream_items[0]["metric_name"], self.random_metric_name)

        wrapper_result = validate_repo_health_metrics(raw_payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], self.random_score)

        audited_data = audit_repository(wrapper_result["metrics"])
        self.assertEqual(audited_data["metric_name"], self.random_metric_name)

        dashboard_output = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

    def test_normalization_and_validation_integration(self):
        alternative_payload = {
            "health_score": round(random.uniform(10.0, 90.0), 2),
            "run_id": f"run_{uuid.uuid4().hex[:6]}"
        }

        wrapper_result = validate_repo_health_metrics(alternative_payload)
        
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], alternative_payload["health_score"])
        self.assertEqual(wrapper_result["metrics"]["metric_name"], alternative_payload["run_id"])
        self.assertIn("timestamp", wrapper_result["metrics"])

        audited = audit_repository(wrapper_result["metrics"])
        dashboard = render_health_dashboard(audited)
        self.assertTrue(dashboard.endswith(".html"))

    def test_invalid_stream_handling(self):
        invalid_payload = {
            "metric_name": f"bad_{uuid.uuid4().hex[:4]}",
            "score": 150.0,
            "timestamp": self.random_timestamp
        }
        
        stream_bytes = json.dumps(invalid_payload).encode('utf-8')
        
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream_bytes)

        wrapper_result = validate_repo_health_metrics(invalid_payload)
        self.assertFalse(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], 150.0)


if __name__ == "__main__":
    unittest.main()