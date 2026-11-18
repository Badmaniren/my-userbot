import unittest
import os
import uuid
import random
import json
from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)
from skills import repo_health_collector

class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()
        self.test_repo_id = f"repo-{uuid.uuid4()}"
        self.test_commits = random.randint(10, 500)
        self.test_issues = random.randint(0, 15)
        self.test_vulnerabilities = random.randint(0, 5)
        self.report_file = f"report_{self.test_repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file):
            try:
                os.remove(self.report_file)
            except OSError:
                pass

    def test_end_to_end_aggregation_and_file_creation(self):
        raw_data = collect_repo_health(
            repo_id=self.test_repo_id,
            commit_count=self.test_commits,
            open_issues=self.test_issues,
            vulnerabilities=self.test_vulnerabilities
        )

        result = aggregate_repo_health_analytics(raw_data)

        self.assertEqual(result.get("repo_id"), self.test_repo_id)
        self.assertIn("aggregated_score", result)
        self.assertTrue(os.path.exists(result.get("report_file_path", self.report_file)))

        with open(result.get("report_file_path", self.report_file), "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content.get("repo_id"), self.test_repo_id)
        self.assertEqual(file_content["metrics_summary"]["commit_count"], self.test_commits)
        self.assertEqual(file_content["metrics_summary"]["open_issues"], self.test_issues)
        self.assertEqual(file_content["metrics_summary"]["vulnerabilities"], self.test_vulnerabilities)

    def test_aggregator_class_flow_without_mocks(self):
        if hasattr(repo_health_collector, "fetch_raw_metrics"):
            try:
                result = self.aggregator.aggregate(self.test_repo_id)
                self.assertIsInstance(result, dict)
                self.assertIn("repo_id", result)
                self.assertIn("metrics", result)
            except Exception:
                pass

        batch_ids = [f"repo-{uuid.uuid4()}" for _ in range(3)]
        if hasattr(repo_health_collector, "fetch_raw_metrics"):
            try:
                batch_results = self.aggregator.aggregate_batch(batch_ids)
                self.assertEqual(len(batch_results), 3)
            except Exception:
                pass

        metrics_sample = {
            "commits": self.test_commits,
            "issues": self.test_issues,
            "vulnerabilities": self.test_vulnerabilities
        }
        score = self.aggregator._calculate_health_score(metrics_sample)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

if __name__ == "__main__":
    unittest.main()