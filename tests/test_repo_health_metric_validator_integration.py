import unittest
import uuid
import random
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
        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_full_metric_lifecycle_and_wrappers(self):
        metric_payload = {
            "metric_name": self.random_metric_name,
            "score": self.random_score,
            "timestamp": self.random_timestamp,
            "extra_metadata": uuid.uuid4().hex
        }

        is_valid = self.validator.validate(metric_payload)
        self.assertTrue(is_valid)

        json_stream = io.BytesIO(f'[{str(metric_payload).replace(chr(39), chr(34))}]'.encode('utf-8'))
        stream_results = self.validator.validate_stream(json_stream)
        self.assertEqual(len(stream_results), 1)
        self.assertEqual(stream_results[0]["metric_name"], self.random_metric_name)
        self.assertEqual(stream_results[0]["score"], self.random_score)

        audited_data = audit_repository(metric_payload)
        self.assertEqual(audited_data["metric_name"], self.random_metric_name)

        dashboard_output = render_health_dashboard(metric_payload)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

        wrapper_result = validate_repo_health_metrics({
            "health_score": self.random_score,
            "run_id": self.random_metric_name
        })
        
        self.assertTrue(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], self.random_score)
        self.assertEqual(wrapper_result["metrics"]["metric_name"], self.random_metric_name)
        self.assertEqual(wrapper_result["metrics"]["timestamp"], 1600000000)

    def test_metric_validation_error_boundaries(self):
        invalid_score = random.choice([-10.0, 105.5, "not_a_number", True])
        bad_payload = {
            "metric_name": f"err_{uuid.uuid4().hex[:4]}",
            "score": invalid_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(bad_payload)

        wrapper_result = validate_repo_health_metrics(bad_payload)
        self.assertFalse(wrapper_result["is_valid"])
        self.assertEqual(wrapper_result["metrics"]["score"], invalid_score)

if __name__ == '__main__':
    unittest.main()