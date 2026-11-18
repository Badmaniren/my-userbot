import unittest
import os
import uuid
import random
from skills import repo_health_collector
from skills import repo_health_analytics_aggregator

class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):
    def test_end_to_end_analytics_pipeline(self):
        random_repo_id = f"repo-{uuid.uuid4()}"
        random_commits = random.randint(10, 500)
        random_issues = random.randint(0, 15)
        random_vulns = random.randint(0, 5)

        raw_data = repo_health_collector.collect_repo_health(
            repo_id=random_repo_id,
            commit_count=random_commits,
            open_issues=random_issues,
            vulnerabilities=random_vulns
        )

        self.assertEqual(raw_data["repo_id"], random_repo_id)
        self.assertEqual(raw_data["commit_count"], random_commits)

        report_data = repo_health_analytics_aggregator.aggregate_repo_health_analytics(raw_data)

        self.assertEqual(report_data["repo_id"], random_repo_id)
        self.assertEqual(report_data["metrics_summary"]["commit_count"], random_commits)
        self.assertEqual(report_data["metrics_summary"]["open_issues"], random_issues)
        self.assertEqual(report_data["metrics_summary"]["vulnerabilities"], random_vulns)

        expected_score = 100.0 - (random_issues * 2.0) - (random_vulns * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0
        self.assertEqual(report_data["aggregated_score"], expected_score)

        report_file_path = report_data.get("report_file_path")
        self.assertTrue(os.path.exists(report_file_path))

        aggregator = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        stream_data = aggregator.aggregate_from_stream(report_file_path)
        self.assertEqual(stream_data["repo_id"], random_repo_id)
        self.assertEqual(stream_data["aggregated_score"], expected_score)

        if os.path.exists(report_file_path):
            os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()