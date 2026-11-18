import unittest
import os
import json
import uuid
import random
from skills import repo_health_analytics_aggregator
from skills import repo_health_collector


class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = str(uuid.uuid4())
        self.commit_count = random.randint(10, 500)
        self.open_issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 3)
        self.report_file_path = f"report_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file_path):
            try:
                os.remove(self.report_file_path)
            except OSError:
                pass

    def test_integration_aggregate_repo_health_analytics_flow(self):
        collected_data = {
            "repo_id": self.repo_id,
            "commit_count": self.commit_count,
            "open_issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities
        }

        result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(collected_data)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        
        expected_score = 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0
        self.assertEqual(result.get("aggregated_score"), expected_score)

        metrics_summary = result.get("metrics_summary", {})
        self.assertEqual(metrics_summary.get("commit_count"), self.commit_count)
        self.assertEqual(metrics_summary.get("open_issues"), self.open_issues)
        self.assertEqual(metrics_summary.get("vulnerabilities"), self.vulnerabilities)

        self.assertIn("aggregated_at", result)

        self.assertTrue(os.path.exists(self.report_file_path), "Файл отчета не был создан")

        with open(self.report_file_path, "r", encoding="utf-8") as f:
            file_data = json.load(f)

        self.assertEqual(file_data.get("repo_id"), self.repo_id)
        self.assertEqual(file_data.get("aggregated_score"), expected_score)
        self.assertEqual(file_data.get("metrics_summary"), metrics_summary)

    def test_integration_collect_repo_health_passthrough(self):
        passthrough_result = repo_health_analytics_aggregator.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )

        self.assertIsInstance(passthrough_result, dict)
        self.assertEqual(passthrough_result.get("repo_id"), self.repo_id)
        self.assertEqual(passthrough_result.get("commit_count"), self.commit_count)
        self.assertEqual(passthrough_result.get("open_issues"), self.open_issues)
        self.assertEqual(passthrough_result.get("vulnerabilities"), self.vulnerabilities)


if __name__ == "__main__":
    unittest.main()