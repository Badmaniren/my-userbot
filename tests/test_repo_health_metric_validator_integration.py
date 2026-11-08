import unittest
import uuid
import random
import io
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

    def test_integration_stream_validation_and_pipeline(self):
        payload_data = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        json_content = json.dumps(payload_data)
        stream = io.BytesIO(json_content.encode('utf-8'))

        validated_list = self.validator.validate_stream(stream)
        self.assertEqual(len(validated_list), 1)
        self.assertEqual(validated_list[0]["metric_name"], self.random_metric_name)
        self.assertEqual(validated_list[0]["score"], self.random_score)

        audited = audit_repository(validated_list[0])
        self.assertEqual(audited["score"], self.random_score)

        dashboard_result = render_health_dashboard(audited)
        self.assertTrue(isinstance(dashboard_result, str))
        self.assertTrue(len(dashboard_result) > 0)

    def test_integration_wrapper_normalization_and_validation(self):
        alt_health_score = round(random.uniform(0.0, 100.0), 2)
        raw_data = {
            "health_score": alt_health_score,
            "run_id": f"run_{uuid.uuid4().hex[:6]}"
        }

        result = validate_repo_health_metrics(raw_data)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["health_score"], alt_health_score)

    def test_integration_invalid_score_exception(self):
        invalid_score = random.uniform(101.0, 200.0)
        bad_data = {
            "metric_name": self.random_metric_name,
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_data)

        wrapper_result = validate_repo_health_metrics(bad_data)
        self.assertFalse(wrapper_result["is_valid"])

if __name__ == "__main__":
    unittest.main()