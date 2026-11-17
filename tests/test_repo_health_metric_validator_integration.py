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
        self.random_score = round(random.uniform(5.0, 95.0), 2)
        self.random_timestamp = random.randint(1600000000, 1700000000)

    def test_end_to_end_metric_flow_and_anti_cheat(self):
        raw_payload = {
            "health_score": self.random_score,
            "run_id": self.random_metric_name,
            "timestamp": self.random_timestamp,
            "extra_anti_cheat_sig": uuid.uuid4().hex
        }

        # Интеграционный вызов обертки валидации
        wrapped_result = validate_repo_health_metrics(raw_payload)
        
        self.assertTrue(wrapped_result["is_valid"], "Metric payload must pass validation after normalization")
        
        validated_metrics = wrapped_result["metrics"]
        self.assertEqual(validated_metrics["score"], self.random_score)
        self.assertEqual(validated_metrics["metric_name"], self.random_metric_name)

        # Сквозной прогон через аудит репозитория
        audited_data = audit_repository(validated_metrics)
        self.assertEqual(audited_data["metric_name"], self.random_metric_name)
        self.assertEqual(audited_data["score"], self.random_score)

        # Сквозной прогон через рендеринг дэшборда
        dashboard_result = render_health_dashboard(audited_data)
        self.assertIsInstance(dashboard_result, str)
        self.assertGreater(len(dashboard_result), 0)

    def test_stream_validation_integration(self):
        stream_data = [
            {
                "metric_name": f"stream_metric_{uuid.uuid4().hex[:6]}",
                "score": round(random.uniform(0.0, 100.0), 2),
                "timestamp": random.randint(1600000000, 1700000000)
            }
        ]
        json_bytes = json.dumps(stream_data).encode('utf-8')
        stream_io = io.BytesIO(json_bytes)

        validated_stream_items = self.validator.validate_stream(stream_io)
        self.assertEqual(len(validated_stream_items), 1)
        self.assertEqual(validated_stream_items[0]["metric_name"], stream_data[0]["metric_name"])

    def test_anti_cheat_out_of_bounds_rejection(self):
        illegal_score = 105.5
        malicious_payload = {
            "metric_name": f"cheat_attempt_{uuid.uuid4().hex[:6]}",
            "score": illegal_score,
            "timestamp": random.randint(1600000000, 1700000000)
        }

        with self.assertRaises(MetricValidationError):
            self.validator.validate(malicious_payload)

        wrapped = validate_repo_health_metrics(malicious_payload)
        self.assertFalse(wrapped["is_valid"])


if __name__ == "__main__":
    unittest.main()