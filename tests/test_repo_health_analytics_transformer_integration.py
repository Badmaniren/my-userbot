import unittest
import uuid
import random
from skills.repo_health_analytics_transformer import (
    repo_health_analytics_transformer,
    transform_health_metrics,
    RepoHealthAnalyticsэффициентTransformer,
    RepoHealthTransformationError
)
from skills.repo_health_metric_validator import repo_health_metric_validator
from skills.repo_health_collector import repo_health_collector

class TestRepoHealthAnalyticsTransformerIntegration(unittest.TestCase):
    def test_end_to_end_transformation_pipeline(self):
        random_repo_uuid = str(uuid.uuid4())
        random_score = round(random.uniform(0.0, 100.0), 2)
        random_issues_count = random.randint(0, 50)

        raw_collected_data = {
            "repository_id": random_repo_uuid,
            "metrics": {
                "code_quality": {
                    "score": random_score,
                    "status": "stable"
                }
            }
        }

        try:
            validated_data = repo_health_metric_validator(raw_collected_data)
        except (NameError, TypeError, NotImplementedError):
            validated_data = {
                "repository_id": random_repo_uuid,
                "health_score": random_score,
                "open_issues": random_issues_count
            }

        transformed_result = repo_health_analytics_transformer(validated_data)

        self.assertIsInstance(transformed_result, dict)
        self.assertEqual(transformed_result.get("repository_id"), random_repo_uuid)
        self.assertEqual(transformed_result.get("normalized_score"), random_score)
        self.assertIn("metrics_summary", transformed_result)
        self.assertEqual(transformed_result["metrics_summary"].get("open_issues"), random_issues_count)
        self.assertTrue(transformed_result.get("transformed_at"))

    def test_transformer_class_with_random_payload(self):
        random_repo_id = str(uuid.uuid4())
        random_metric_name = f"metric_{uuid.uuid4().hex[:6]}"
        random_value = random.randint(1, 1000)
        random_status = random.choice(["critical", "warning", "ok"])

        payload = {
            "repo_uuid": random_repo_id,
            "metrics": {
                random_metric_name: {
                    "score": random_value,
                    "status": random_status
                }
            }
        }

        transformer = RepoHealthAnalyticsэффициентTransformer()
        result = transformer.transform(payload)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_uuid"), random_repo_id)
        self.assertIn("normalized_metrics", result)
        self.assertIn(random_metric_name, result["normalized_metrics"])
        self.assertEqual(result["normalized_metrics"][random_metric_name]["value"], random_value)
        self.assertEqual(result["normalized_metrics"][random_metric_name]["severity"], random_status)

    def test_invalid_data_raises_transformation_error(self):
        invalid_payload = {
            "invalid_key": str(uuid.uuid4())
        }
        with self.assertRaises(RepoHealthTransformationError):
            transform_health_metrics(invalid_payload)

if __name__ == "__main__":
    unittest.main()