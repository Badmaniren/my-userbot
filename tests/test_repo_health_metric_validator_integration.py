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
        self.random_id = str(uuid.uuid4())
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = int(random.randint(1600000000, 1700000000))

    def test_end_to_end_metric_pipeline(self):
        raw_metric = {
            "run_id": self.random_id,
            "health_score": self.random_score,
            "timestamp": self.random_timestamp
        }

        validation_result = validate_repo_health_metrics(raw_metric)
        self.assertTrue(validation_result["is_valid"], "Pipeline should successfully normalize and validate payload")
        
        normalized_metric = validation_result["metrics"]
        self.assertEqual(normalized_metric["metric_name"], self.random_id)
        self.assertEqual(normalized_metric["score"], self.random_score)

        audited = audit_repository(normalized_metric)
        self.assertEqual(audited["metric_name"], self.random_id)

        dashboard_output = render_health_dashboard(audited)
        self.assertIn(self.random_id, dashboard_output)
        self.assertIn(str(self.random_score), dashboard_output)

    def test_stream_processing_integration(self):
        metrics_stream = [
            {
                "metric_name": f"metric_{uuid.uuid4()}",
                "score": round(random.uniform(10.0, 90.0), 2),
                "timestamp": int(random.randint(1600000000, 1700000000))
            }
            for _ in range(3)
        ]
        stream_payload = json.dumps(metrics_stream)

        validated_stream = self.validator.validate_stream(stream_payload)
        self.assertEqual(len(validated_stream), 3)
        self.assertEqual(validated_stream[0]["metric_name"], metrics_stream[0]["metric_name"])

    def test_invalid_metric_rejection_pipeline(self):
        invalid_metric = {
            "metric_name": self.random_id,
            "score": 105.5,
            "timestamp": self.random_timestamp
        }

        validation_result = validate_repo_health_metrics(invalid_metric)
        self.assertFalse(validation_result["is_valid"])

        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_metric)

if __name__ == "__main__":
    unittest.main()