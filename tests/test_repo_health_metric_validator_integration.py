import unittest
import json
import uuid
import random
from skills.repo_health_metric_validator import (
    RepoHealthMetricValidator,
    MetricValidationError,
    validate_repo_health_metrics,
    audit_repository,
    render_health_dashboard
)


class IntegrationTestRepoHealthMetricValidator(unittest.TestCase):

    def setUp(self):
        self.validator = RepoHealthMetricValidator()
        self.unique_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_full_metric_pipeline_and_downstream_integration(self):
        payload = {
            "metric_name": self.unique_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "metadata": {
                "session_uuid": str(uuid.uuid4()),
                "check_id": random.randint(1000, 9999)
            }
        }

        stream_data = json.dumps(payload)
        
        validated_list = self.validator.validate_stream(stream_data)
        self.assertEqual(len(validated_list), 1)
        self.assertEqual(validated_list[0]["metric_name"], self.unique_metric_name)
        self.assertEqual(validated_list[0]["score"], self.random_score)

        wrapper_result = validate_repo_health_metrics(payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["metric_name"], self.unique_metric_name)

        audited_data = audit_repository(wrapper_result["metrics"])
        self.assertIn("metric_name", audited_data)
        self.assertEqual(audited_data["score"], self.random_score)

        dashboard_output = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

    def test_normalization_and_invalid_score_boundaries(self):
        alt_payload = {
            "health_score": round(random.uniform(0.0, 100.0), 2),
            "run_id": f"run_{uuid.uuid4().hex[:6]}"
        }

        wrapper_result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], alt_payload["health_score"])
        self.assertEqual(wrapper_result["metrics"]["metric_name"], alt_payload["run_id"])
        self.assertEqual(wrapper_result["metrics"]["timestamp"], 1600000000)

        invalid_payload = {
            "metric_name": self.unique_metric_name,
            "score": 105.5,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_payload)

        invalid_stream = "not a json string {"
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(invalid_stream)


if __name__ == "__main__":
    unittest.main()