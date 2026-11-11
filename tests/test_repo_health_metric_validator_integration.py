import unittest
import uuid
import random
import json
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

    def test_validate_success_with_randomized_payload(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        result = self.validator.validate(payload)
        self.assertTrue(result)

    def test_validate_stream_with_multiple_random_metrics(self):
        metrics_list = [
            {
                "metric_name": f"stream_metric_{uuid.uuid4().hex[:6]}",
                "score": round(random.uniform(10.0, 90.0), 2),
                "timestamp": self.random_timestamp
            },
            {
                "metric_name": f"stream_metric_{uuid.uuid4().hex[:6]}",
                "score": round(random.uniform(0.0, 50.0), 2),
                "timestamp": self.random_timestamp + 100
            }
        ]
        stream_data = json.dumps(metrics_list)
        stream_io = io.BytesIO(stream_data.encode('utf-8'))

        validated = self.validator.validate_stream(stream_io)
        self.assertEqual(len(validated), 2)
        self.assertEqual(validated[0]["metric_name"], metrics_list[0]["metric_name"])
        self.assertEqual(validated[1]["score"], metrics_list[1]["score"])

    def test_validate_repo_health_metrics_normalization(self):
        random_health_score = round(random.uniform(20.0, 95.0), 2)
        random_run_id = f"run_{uuid.uuid4().hex[:8]}"

        unnormalized_payload = {
            "health_score": random_health_score,
            "run_id": random_run_id
        }

        result = validate_repo_health_metrics(unnormalized_payload)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], random_health_score)
        self.assertEqual(result["metrics"]["metric_name"], random_run_id)
        self.assertIn("timestamp", result["metrics"])

    def test_audit_and_render_pipeline_integration(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "custom_meta": uuid.uuid4().hex
        }

        audited_data = audit_repository(payload)
        self.assertEqual(audited_data["custom_meta"], payload["custom_meta"])

        dashboard_path = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_path, str)
        self.assertTrue(len(dashboard_path) > 0)


if __name__ == "__main__":
    unittest.main()