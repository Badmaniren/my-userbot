import unittest
import uuid
import random
import json
from io import BytesIO, StringIO
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

    def test_validate_success_and_failure_flow(self):
        valid_metric = {
            "metric_name": self.random_id,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }
        
        self.assertTrue(self.validator.validate(valid_metric))

        invalid_data_types = [
            ("not a dict", MetricValidationError),
            ({"metric_name": self.random_id, "timestamp": self.random_timestamp}, MetricValidationError),
            ({"metric_name": self.random_id, "score": "high", "timestamp": self.random_timestamp}, MetricValidationError),
            ({"metric_name": self.random_id, "score": 105.5, "timestamp": self.random_timestamp}, MetricValidationError),
        ]

        for bad_data, expected_exception in invalid_data_types:
            with self.subTest(bad_data=bad_data):
                with self.assertRaises(expected_exception):
                    self.validator.validate(bad_data)

    def test_validate_stream_integration(self):
        stream_payload = [
            {
                "metric_name": f"metric_{uuid.uuid4()}",
                "score": round(random.uniform(10.0, 90.0), 2),
                "timestamp": random.randint(1500000000, 1800000000)
            },
            {
                "metric_name": f"metric_{uuid.uuid4()}",
                "score": round(random.uniform(10.0, 90.0), 2),
                "timestamp": random.randint(1500000000, 1800000000)
            }
        ]

        json_bytes = json.dumps(stream_payload).encode('utf-8')
        stream = BytesIO(json_bytes)

        validated_results = self.validator.validate_stream(stream)
        self.assertEqual(len(validated_results), 2)
        self.assertEqual(validated_results[0]["metric_name"], stream_payload[0]["metric_name"])
        self.assertEqual(validated_results[1]["metric_name"], stream_payload[1]["metric_name"])

        string_stream = StringIO(json.dumps(stream_payload[0]))
        single_result = self.validator.validate_stream(string_stream)
        self.assertEqual(len(single_result), 1)
        self.assertEqual(single_result[0]["score"], stream_payload[0]["score"])

    def test_validate_repo_health_metrics_wrapper(self):
        raw_data = {
            "health_score": self.random_score,
            "run_id": self.random_id
        }

        result = validate_repo_health_metrics(raw_data)
        
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["score"], self.random_score)
        self.assertEqual(result["metrics"]["metric_name"], self.random_id)
        self.assertIn("timestamp", result["metrics"])

    def test_audit_repository_and_dashboard_integration(self):
        metrics_payload = {
            "metric_name": self.random_id,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        audited = audit_repository(metrics_payload)
        self.assertEqual(audited["metric_name"], self.random_id)
        self.assertEqual(audited["score"], self.random_score)

        dashboard_output = render_health_dashboard(audited)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

if __name__ == "__main__":
    unittest.main()