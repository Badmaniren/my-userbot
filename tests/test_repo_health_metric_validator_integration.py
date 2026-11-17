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
        self.metric_name_slug = f"metric_test_{uuid.uuid4().hex[:8]}"
        self.random_score = round(random.uniform(0.0, 100.0), 2)
        self.random_timestamp = random.randint(1500000000, 1800000000)

    def test_full_metric_pipeline_lifecycle(self):
        payload = {
            "metric_name": self.metric_name_slug,
            "score": self.random_score,
            "timestamp": self.random_timestamp
        }

        # 1. Validate through main validator class
        is_valid = self.validator.validate(payload)
        self.assertTrue(is_valid)

        # 2. Process via audit repository function
        audited_result = audit_repository(payload)
        self.assertEqual(audited_result["metric_name"], self.metric_name_slug)
        self.assertEqual(audited_result["score"], self.random_score)

        # 3. Render dashboard integration check
        dashboard_output = render_health_dashboard(payload)
        self.assertIn(self.metric_name_slug, dashboard_output)
        self.assertIn(str(self.random_score), dashboard_output)

        # 4. Alternative normalization validator pipeline integration
        alt_payload = {
            "run_id": self.metric_name_slug,
            "health_score": self.random_score,
            "timestamp": self.random_timestamp
        }
        normalized_result = validate_repo_health_metrics(alt_payload)
        self.assertTrue(normalized_result["is_valid"])
        self.assertEqual(normalized_result["metrics"]["metric_name"], self.metric_name_slug)
        self.assertEqual(normalized_result["metrics"]["score"], self.random_score)

        # 5. Stream processing integration test (IO stream bytes)
        stream_data = json.dumps([payload]).encode('utf-8')
        stream = io.BytesIO(stream_data)
        stream_validated = self.validator.validate_stream(stream)
        self.assertEqual(len(stream_validated), 1)
        self.assertEqual(stream_validated[0]["metric_name"], self.metric_name_slug)

    def test_invalid_metric_rejections(self):
        bad_score = round(random.uniform(101.0, 500.0), 2)
        invalid_payload = {
            "metric_name": f"fail_metric_{uuid.uuid4().hex[:6]}",
            "score": bad_score,
            "timestamp": self.random_timestamp
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(invalid_payload)

        alt_invalid_payload = {
            "health_score": bad_score,
            "timestamp": self.random_timestamp
        }
        res = validate_repo_health_metrics(alt_invalid_payload)
        self.assertFalse(res["is_valid"])


if __name__ == "__main__":
    unittest.main()