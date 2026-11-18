import unittest
import json
import uuid
import random
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
        self.metric_name_seed = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1600000000, 1700000000)

    def test_end_to_end_metric_lifecycle_and_pipeline(self):
        raw_metric = {
            "metric_name": self.metric_name_seed,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        audited = audit_repository(raw_metric)
        self.assertEqual(audited["metric_name"], self.metric_name_seed)
        self.assertEqual(audited["score"], self.random_score)

        dashboard_output = render_health_dashboard(audited)
        self.assertIn(self.metric_name_seed, dashboard_output)
        self.assertIn(str(self.random_score), dashboard_output)

        stream_data = json.dumps([raw_metric])
        validated_stream = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_stream), 1)
        self.assertEqual(validated_stream[0]["metric_name"], self.metric_name_seed)

    def test_payload_normalization_and_resilience_integration(self):
        alternative_payload = {
            "run_id": f"run_{uuid.uuid4().hex[:6]}",
            "health_score": round(random.uniform(10.0, 90.0), 2),
            "timestamp": self.random_timestamp
        }

        result = validate_repo_health_metrics(alternative_payload)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], alternative_payload["run_id"])
        self.assertEqual(result["metrics"]["score"], alternative_payload["health_score"])

    def test_invalid_stream_and_metric_rejection(self):
        bad_score = round(random.uniform(101.0, 500.0), 2)
        invalid_metric = {
            "metric_name": f"err_{uuid.uuid4().hex[:4]}",
            "score": bad_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_metric)

        res = validate_repo_health_metrics(invalid_metric)
        self.assertFalse(res["is_valid"])

        corrupted_stream = f"{{invalid_json_{uuid.uuid4().hex}}}"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(corrupted_stream)

if __name__ == "__main__":
    unittest.main()