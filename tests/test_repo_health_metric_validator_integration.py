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
        self.metric_name_rand = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_end_to_end_metric_validation_and_pipeline(self):
        payload = {
            "metric_name": self.metric_name_rand,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "metadata": {
                "run_uuid": str(uuid.uuid4())
            }
        }

        is_valid = self.validator.validate(payload)
        self.assertTrue(is_valid)

        stream_data = json.dumps([payload])
        stream = io.StringIO(stream_data)
        validated_stream_result = self.validator.validate_stream(stream)
        
        self.assertEqual(len(validated_stream_result), 1)
        self.assertEqual(validated_stream_result[0]["metric_name"], self.metric_name_rand)
        self.assertEqual(validated_stream_result[0]["score"], self.random_score)

        audited_data = audit_repository(payload)
        self.assertEqual(audited_data["metric_name"], self.metric_name_rand)

        dashboard_result = render_health_dashboard(payload)
        self.assertIsInstance(dashboard_result, str)
        self.assertTrue(len(dashboard_result) > 0)

        wrapper_payload = {
            "health_score": self.random_score,
            "run_id": f"run_{uuid.uuid4().hex[:6]}"
        }
        wrapped_result = validate_repo_health_metrics(wrapper_payload)
        self.assertIn("is_valid", wrapped_result)
        self.assertTrue(wrapped_result["is_valid"])
        self.assertEqual(wrapped_result["metrics"]["health_score"], self.random_score)

    def test_invalid_metric_boundaries_and_types(self):
        out_of_bounds_high = {
            "metric_name": f"bad_metric_{uuid.uuid4().hex[:4]}",
            "score": 105.5,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(out_of_bounds_high)

        out_of_bounds_low = {
            "metric_name": f"bad_metric_{uuid.uuid4().hex[:4]}",
            "score": -5.0,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(out_of_bounds_low)

        missing_field = {
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(missing_field)


if __name__ == "__main__":
    unittest.main()