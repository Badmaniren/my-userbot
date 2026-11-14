import unittest
import uuid
import random
import json
import os
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
        self.random_id = str(uuid.uuid4())
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_end_to_end_metric_pipeline(self):
        payload = {
            "metric_name": f"metric_{self.random_id}",
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        # 1. Validate through class method
        is_valid = self.validator.validate(payload)
        self.assertTrue(is_valid)

        # 2. Process via stream simulation (JSON string)
        stream_data = json.dumps([payload])
        validated_stream = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_stream), 1)
        self.assertEqual(validated_stream[0]["metric_name"], payload["metric_name"])

        # 3. Pass to integration wrapper
        wrapper_result = validate_repo_health_metrics(payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], self.random_score)

        # 4. Pass through auditor and dashboard rendering (real function invocation)
        audit_res = audit_repository(wrapper_result["metrics"])
        self.assertEqual(audit_res["metric_name"], payload["metric_name"])

        dashboard_output = render_health_dashboard(audit_res)
        self.assertTrue(isinstance(dashboard_output, str))
        self.assertTrue(len(dashboard_output) > 0)

    def test_normalization_and_fault_tolerance(self):
        alt_payload = {
            "run_id": f"run_{self.random_id}",
            "health_score": self.random_score
        }

        wrapper_result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], self.random_score)
        self.assertEqual(wrapper_result["metrics"]["metric_name"], f"run_{self.random_id}")
        self.assertEqual(wrapper_result["metrics"]["timestamp"], 1600000000)

    def test_invalid_data_handling(self):
        bad_payload = {
            "metric_name": f"bad_{self.random_id}",
            "score": 150.0,  # Out of bounds
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        wrapper_result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(wrapper_result["is_valid"])

if __name__ == "__main__":
    unittest.main()