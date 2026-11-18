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
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = str(uuid.uuid1())

    def test_end_to_end_metric_lifecycle_and_rendering(self):
        payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        validation_result = validate_repo_health_metrics(payload)
        self.assertTrue(validation_result["is_valid"])
        self.assertEqual(validation_result["metrics"]["metric_name"], self.random_metric_name)
        self.assertEqual(validation_result["metrics"]["score"], self.random_score)

        audited = audit_repository(payload)
        self.assertEqual(audited["metric_name"], self.random_metric_name)

        dashboard_output = render_health_dashboard(payload)
        self.assertIn(self.random_metric_name, dashboard_output)
        self.assertIn(str(self.random_score), dashboard_output)

    def test_stream_processing_and_validation(self):
        stream_data = [
            {
                "metric_name": f"stream_metric_{uuid.uuid4().hex[:6]}",
                "score": round(random.uniform(10.0, 90.0), 2),
                "timestamp": uuid.uuid4().hex
            },
            {
                "metric_name": f"stream_metric_{uuid.uuid4().hex[:6]}",
                "score": round(random.uniform(10.0, 90.0), 2),
                "timestamp": uuid.uuid4().hex
            }
        ]
        
        json_stream = json.dumps(stream_data)
        validated_stream = self.validator.validate_stream(json_stream)
        
        self.assertEqual(len(validated_stream), 2)
        self.assertEqual(validated_stream[0]["metric_name"], stream_data[0]["metric_name"])
        self.assertEqual(validated_stream[1]["metric_name"], stream_data[1]["metric_name"])

    def test_payload_transformation_integration(self):
        alt_payload = {
            "run_id": f"run_{uuid.uuid4().hex[:8]}",
            "health_score": round(random.uniform(50.0, 100.0), 2),
            "timestamp": uuid.uuid4().hex
        }

        result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(result["is_valid"])
        self.assertEqual(result["metrics"]["metric_name"], alt_payload["run_id"])
        self.assertEqual(result["metrics"]["score"], alt_payload["health_score"])

    def test_invalid_metric_handling(self):
        invalid_payload = {
            "metric_name": f"bad_{uuid.uuid4().hex[:4]}",
            "score": 150.0,
            "timestamp": uuid.uuid4().hex
        }

        result = validate_repo_health_metrics(invalid_payload)
        self.assertFalse(result["is_valid"])
        
        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_payload)

if __name__ == "__main__":
    unittest.main()