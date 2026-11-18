import unittest
import uuid
import random
from skills.repo_health_metric_validator import repo_health_metric_validator
from skills.repo_health_analytics_transformer import repo_health_analytics_transformer

class TestRepoHealthAnalyticsTransformerIntegration(unittest.TestCase):
    def test_transformation_pipeline_integration(self):
        unique_repo_id = f"repo-{uuid.uuid4()}"
        random_score = round(random.uniform(50.0, 100.0), 2)
        random_issues_count = random.randint(0, 15)

        raw_metrics = {
            "repository_id": unique_repo_id,
            "health_score": random_score,
            "open_issues": random_issues_count,
            "status": "active"
        }

        validated_metrics = repo_health_metric_validator(raw_metrics)
        normalized_report = repo_health_analytics_transformer(validated_metrics)

        self.assertIsInstance(normalized_report, dict)
        self.assertEqual(normalized_report.get("repository_id"), unique_repo_id)
        self.assertEqual(normalized_report.get("normalized_score"), random_score)
        self.assertEqual(normalized_report.get("metrics_summary", {}).get("open_issues"), random_issues_count)
        self.assertIn("transformed_at", normalized_report)

if __name__ == "__main__":
    unittest.main()