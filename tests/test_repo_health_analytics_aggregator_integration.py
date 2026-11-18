import unittest
import uuid
import random
import os
import json
from skills import repo_health_collector
from skills import repo_health_analytics_aggregator

class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.commit_count = random.randint(1, 150)
        self.open_issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 3)
        self.report_file = f"report_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file):
            try:
                os.remove(self.report_file)
            except OSError:
                pass

    def test_end_to_end_aggregation_and_reporting(self):
        raw_data = repo_health_collector.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )

        self.assertEqual(raw_data["repo_id"], self.repo_id)
        self.assertEqual(raw_data["commit_count"], self.commit_count)

        report_result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(raw_data)

        self.assertEqual(report_result["repo_id"], self.repo_id)
        self.assertIn("aggregated_score", report_result)
        self.assertIn("metrics_summary", report_result)
        self.assertEqual(report_result["metrics_summary"]["commit_count"], self.commit_count)
        self.assertEqual(report_result["metrics_summary"]["open_issues"], self.open_issues)
        self.assertEqual(report_result["metrics_summary"]["vulnerabilities"], self.vulnerabilities)

        expected_score = 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0
        self.assertEqual(report_result["aggregated_score"], expected_score)

        self.assertTrue(os.path.exists(self.report_file))

        with open(self.report_file, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["repo_id"], self.repo_id)
        self.assertEqual(file_content["aggregated_score"], expected_score)
        self.assertEqual(file_content["metrics_summary"]["open_issues"], self.open_issues)

if __name__ == "__main__":
    unittest.main()