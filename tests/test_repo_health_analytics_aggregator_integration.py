import unittest
import os
import uuid
import random
from skills import repo_health_analytics_aggregator
from skills import repo_health_collector


class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.commit_count = random.randint(10, 500)
        self.open_issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 3)
        self.report_file_path = f"report_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file_path):
            os.remove(self.report_file_path)

    def test_aggregate_repo_health_analytics_integration(self):
        collected_data = {
            "repo_id": self.repo_id,
            "commit_count": self.commit_count,
            "open_issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities
        }

        result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(collected_data)

        self.assertEqual(result.get("repo_id"), self.repo_id)
        
        expected_score = float(100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0))
        if expected_score < 0.0:
            expected_score = 0.0
            
        self.assertEqual(result.get("aggregated_score"), expected_score)
        
        summary = result.get("metrics_summary", {})
        self.assertEqual(summary.get("commit_count"), self.commit_count)
        self.assertEqual(summary.get("open_issues"), self.open_issues)
        self.assertEqual(summary.get("vulnerabilities"), self.vulnerabilities)

        self.assertTrue(os.path.exists(self.report_file_path), "Файл отчета должен быть создан на диске")

    def test_aggregator_class_and_collector_interaction(self):
        aggregator = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        
        collected = repo_health_analytics_aggregator.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )
        
        self.assertIsInstance(collected, dict)
        self.assertEqual(collected.get("repo_id"), self.repo_id)

        agg_result = aggregator.aggregate(self.repo_id)
        self.assertEqual(agg_result.get("repo_id"), self.repo_id)
        self.assertIn("metrics", agg_result)
        self.assertIn("aggregated_at", agg_result)


if __name__ == "__main__":
    unittest.main()