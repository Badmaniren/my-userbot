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
        self.random_id = str(uuid.uuid4())
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_end_to_end_metric_flow(self):
        payload = {
            "metric_name": f"metric_{self.random_id}",
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        # 1. Validate stream ingestion (testing validate_stream directly with real JSON bytes)
        json_bytes = json.dumps(payload).encode('utf-8')
        stream = io.BytesIO(json_bytes)
        validated_stream_data = self.validator.validate_stream(stream)
        
        self.assertEqual(len(validated_stream_data), 1)
        self.assertEqual(validated_stream_data[0]["metric_name"], payload["metric_name"])
        self.assertEqual(validated_stream_data[0]["score"], self.random_score)

        # 2. Pass through wrapper for normalization and validation
        normalization_input = {
            "run_id": f"run_{self.random_id}",
            "health_score": self.random_score
        }
        wrapped_result = validate_repo_health_metrics(normalization_input)
        
        self.assertTrue(wrapped_result["is_valid"])
        self.assertEqual(wrapped_result["metrics"]["score"], self.random_score)
        self.assertEqual(wrapped_result["metrics"]["metric_name"], f"run_{self.random_id}")
        self.assertEqual(wrapped_result["metrics"]["timestamp"], 1600000000)

        # 3. Audit repository pipeline integration
        audited = audit_repository(wrapped_result["metrics"])
        self.assertEqual(audited["metric_name"], f"run_{self.random_id}")

        # 4. Render health dashboard integration
        dashboard_res = render_health_dashboard(audited)
        self.assertIsInstance(dashboard_res, str)
        self.assertTrue(len(dashboard_res) > 0)

    def test_anti_cheat_boundary_violations(self):
        out_of_bounds_score = 105.5
        cheat_payload = {
            "metric_name": f"cheat_attempt_{self.random_id}",
            "score": out_of_bounds_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(cheat_payload)

        wrapped_result = validate_repo_health_metrics(cheat_payload)
        self.assertFalse(wrapped_result["is_valid"])
        self.assertEqual(wrapped_result["metrics"]["score"], out_of_bounds_score)


if __name__ == "__main__":
    unittest.main()