import unittest
import os
import uuid
import random
import json
from skills import repo_health_analytics_aggregator
from skills import repo_health_collector

class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.commit_count = random.randint(10, 500)
        self.open_issues = random.randint(0, 15)
        self.vulnerabilities = random.randint(0, 3)
        self.report_file_path = f"report_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file_path):
            try:
                os.remove(self.report_file_path)
            except OSError:
                pass

    def test_integration_aggregation_and_reporting_flow(self):
        if hasattr(repo_health_collector, "collect_repo_health"):
            raw_data = repo_health_collector.collect_repo_health(
                repo_id=self.repo_id,
                commit_count=self.commit_count,
                open_issues=self.open_issues,
                vulnerabilities=self.vulnerabilities
            )
        else:
            raw_data = {
                "repo_id": self.repo_id,
                "commit_count": self.commit_count,
                "open_issues": self.open_issues,
                "vulnerabilities": self.vulnerabilities
            }

        result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(raw_data)

        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertIn("aggregated_score", result)
        self.assertIsInstance(result["aggregated_score"], float)

        metrics_summary = result.get("metrics_summary", {})
        self.assertEqual(metrics_summary.get("commit_count"), self.commit_count)
        self.assertEqual(metrics_summary.get("open_issues"), self.open_issues)
        self.assertEqual(metrics_summary.get("vulnerabilities"), self.vulnerabilities)

        self.assertTrue(os.path.exists(self.report_file_path))

        with open(self.report_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content.get("repo_id"), self.repo_id)
        self.assertEqual(file_content.get("aggregated_score"), result["aggregated_score"])
        self.assertEqual(file_content.get("metrics_summary", {}).get("open_issues"), self.open_issues)

    def test_aggregator_class_methods(self):
        aggregator = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        
        aggregated_result = aggregator.aggregate(self.repo_id)
        self.assertEqual(aggregated_result.get("repo_id"), self.repo_id)
        self.assertIn("metrics", aggregated_result)
        self.assertIn("aggregated_at", aggregated_result)

        batch_result = aggregator.aggregate_batch([self.repo_id, f"repo-{uuid.uuid4()}"])
        self.assertIsInstance(batch_result, list)
        self.assertGreaterEqual(len(batch_result), 2)
        
        found_target = False
        for item in batch_result:
            if item.get("repo_id") == self.repo_id:
                found_target = True
                self.assertIn("metrics", item)
        self.assertTrue(found_target)

if __name__ == "__main__":
    unittest.main()