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

    def test_end_to_end_metric_validation_and_pipeline(self):
        unique_metric_name = f"metric_test_{uuid.uuid4().hex[:8]}"
        random_score = round(random.uniform(1.0, 99.0), 2)
        random_timestamp = random.randint(1500000000, 1800000000)

        raw_payload = {
            "metric_name": unique_metric_name,
            "score": random_score,
            "timestamp": random_timestamp,
            "extra_diagnostic_field": uuid.uuid4().hex
        }

        validator = RepoHealthMetricValidator()
        stream_data = json.dumps([raw_payload])
        stream = io.StringIO(stream_data)

        validated_stream_results = validator.validate_stream(stream)
        self.assertEqual(len(validated_stream_results), 1)
        self.assertEqual(validated_stream_results[0]["metric_name"], unique_metric_name)
        self.assertEqual(validated_stream_results[0]["score"], random_score)

        wrapper_result = validate_repo_health_metrics(raw_payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["metric_name"], unique_metric_name)
        self.assertEqual(wrapper_result["metrics"]["score"], random_score)

        audited_data = audit_repository(wrapper_result["metrics"])
        self.assertEqual(audited_data["metric_name"], unique_metric_name)

        dashboard_output = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

        alt_payload = {
            "health_score": random.uniform(0.0, 100.0),
            "run_id": f"run_{uuid.uuid4().hex[:6]}"
        }
        alt_wrapper_result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(alt_wrapper_result["is_valid"])
        self.assertIn("score", alt_wrapper_result["metrics"])
        self.assertIn("metric_name", alt_wrapper_result["metrics"])

    def test_invalid_metric_boundaries_and_types(self):
        validator = RepoHealthMetricValidator()

        out_of_bounds_score = 105.5
        invalid_metric = {
            "metric_name": f"fail_metric_{uuid.uuid4().hex[:4]}",
            "score": out_of_bounds_score,
            "timestamp": random.randint(1500000000, 1800000000)
        }

        with self.assertRaises(MetricValidationError):
            validator.validate(invalid_metric)

        wrapper_fail_result = validate_repo_health_metrics(invalid_metric)
        self.assertFalse(wrapper_fail_result["is_valid"])

        invalid_type_metric = {
            "metric_name": "type_fail",
            "score": "not_a_number",
            "timestamp": 1600000000
        }

        with self.assertRaises(MetricValidationError):
            validator.validate(invalid_type_metric)

if __name__ == "__main__":
    unittest.main()