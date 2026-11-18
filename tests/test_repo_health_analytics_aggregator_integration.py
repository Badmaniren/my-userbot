import unittest
import uuid
import random
import os
import json
from skills import repo_health_analytics_aggregator
from skills import repo_health_collector


class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.commit_count = random.randint(10, 500)
        self.open_issues = random.randint(0, 5)
        self.vulnerabilities = random.randint(0, 2)
        
        if hasattr(repo_health_collector, "collect_repo_health"):
            self.raw_data = repo_health_collector.collect_repo_health(
                repo_id=self.repo_id,
                commit_count=self.commit_count,
                open_issues=self.open_issues,
                vulnerabilities=self.vulnerabilities
            )
        else:
            self.raw_data = {
                "repo_id": self.repo_id,
                "commit_count": self.commit_count,
                "open_issues": self.open_issues,
                "vulnerabilities": self.vulnerabilities
            }

        if hasattr(repo_health_collector, "fetch_raw_metrics"):
            setattr(repo_health_collector, "fetch_raw_metrics", lambda rid: {
                "repo_id": rid,
                "commits": self.commit_count,
                "issues": self.open_issues,
                "vulnerabilities": self.vulnerabilities,
                "status": "active"
            })

        self.aggregator = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        self.report_file = f"report_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file):
            try:
                os.remove(self.report_file)
            except OSError:
                pass

    def test_aggregate_repo_health_analytics_integration(self):
        result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(self.raw_data)
        
        self.assertEqual(result.get("repo_id"), self.repo_id)
        
        expected_score = 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0
            
        self.assertEqual(result.get("aggregated_score"), expected_score)
        
        metrics_summary = result.get("metrics_summary", {})
        self.assertEqual(metrics_summary.get("commit_count"), self.commit_count)
        self.assertEqual(metrics_summary.get("open_issues"), self.open_issues)
        self.assertEqual(metrics_summary.get("vulnerabilities"), self.vulnerabilities)

        report_path = result.get("report_file_path")
        self.assertTrue(os.path.exists(report_path))
        
        with open(report_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)
            self.assertEqual(file_content.get("repo_id"), self.repo_id)
            self.assertEqual(file_content.get("aggregated_score"), expected_score)

    def test_aggregator_class_methods_integration(self):
        aggregated_result = self.aggregator.aggregate(self.repo_id)
        self.assertEqual(aggregated_result.get("repo_id"), self.repo_id)
        
        metrics = aggregated_result.get("metrics", {})
        self.assertEqual(metrics.get("commits"), self.commit_count)
        self.assertEqual(metrics.get("issues"), self.open_issues)
        self.assertEqual(metrics.get("vulnerabilities"), self.vulnerabilities)

        score = self.aggregator._calculate_health_score(metrics)
        self.assertIsInstance(score, float)
        self.assertTrue(0.0 <= score <= 100.0)

        batch_result = self.aggregator.aggregate_batch([self.repo_id])
        self.assertIsInstance(batch_result, list)
        self.assertEqual(len(batch_result), 1)
        self.assertEqual(batch_result[0].get("repo_id"), self.repo_id)


if __name__ == "__main__":
    unittest.main()