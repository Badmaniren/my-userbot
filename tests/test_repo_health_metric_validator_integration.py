import io
import json
import random
import unittest
import uuid

from skills.repo_health_metric_validator import (
    MetricValidationError,
    RepoHealthMetricValidator,
    audit_repository,
    render_health_dashboard,
    validate_repo_health_metrics,
)


class TestRepoHealthMetricValidatorIntegration(unittest.TestCase):
    def setUp(self):
        self.validator = RepoHealthMetricValidator()

    def test_integration_flow_with_random_data(self):
        random_run_id = f"run-{uuid.uuid4()}"
        random_score = round(random.uniform(0.0, 100.0), 2)
        random_timestamp = random.randint(1600000000, 1700000000)

        input_metrics = {
            "run_id": random_run_id,
            "health_score": random_score,
            "timestamp": random_timestamp,
        }

        result = validate_repo_health_metrics(input_metrics)

        self.assertTrue(result.get("is_valid"))
        self.assertEqual(result["metrics"]["score"], random_score)
        self.assertEqual(result["metrics"]["run_id"], random_run_id)

        audit_result = audit_repository(result["metrics"])
        self.assertEqual(audit_result["score"], random_score)

        dashboard_output = render_health_dashboard(audit_result)
        self.assertIsInstance(dashboard_output, str)
        self.assertTrue(len(dashboard_output) > 0)

    def test_validate_stream_bytes_and_str(self):
        count = random.randint(3, 7)
        generated_items = []
        for _ in range(count):
            generated_items.append(
                {
                    "metric_name": f"metric_{uuid.uuid4()}",
                    "score": round(random.uniform(1.0, 99.0), 4),
                    "timestamp": random.randint(1000000, 2000000),
                }
            )

        json_bytes = json.dumps(generated_items).encode("utf-8")
        stream = io.BytesIO(json_bytes)

        validated_list = self.validator.validate_stream(stream)
        self.assertEqual(len(validated_list), count)
        for original, validated in zip(generated_items, validated_list):
            self.assertEqual(validated["metric_name"], original["metric_name"])
            self.assertEqual(validated["score"], original["score"])

    def test_validate_out_of_bounds_score(self):
        metric_name = f"metric_invalid_{uuid.uuid4()}"
        invalid_score_low = -round(random.uniform(0.1, 100.0), 2)
        invalid_score_high = round(random.uniform(100.1, 500.0), 2)

        payload_low = {
            "metric_name": metric_name,
            "score": invalid_score_low,
            "timestamp": 1600000000,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload_low)

        payload_high = {
            "metric_name": metric_name,
            "score": invalid_score_high,
            "timestamp": 1600000000,
        }
        with self.assertRaises(MetricValidationError):
            self.validator.validate(payload_high)

    def test_validate_invalid_stream_format(self):
        invalid_json = f"invalid_json_{uuid.uuid4()}"
        stream = io.StringIO(invalid_json)
        with self.assertRaises(MetricValidationError):
            self.validator.validate_stream(stream)


if __name__ == "__main__":
    unittest.main()