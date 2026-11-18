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
        self.open_issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 3)
        self.report_file = f"report_{self.repo_id}.json"

    def tearDown(self):
        if os.path.exists(self.report_file):
            try:
                os.remove(self.report_file)
            except OSError:
                pass

    def test_integration_flow_without_mocks(self):
        collected_data = repo_health_collector.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )

        self.assertEqual(collected_data["repo_id"], self.repo_id)
        self.assertEqual(collected_data["commit_count"], self.commit_count)
        self.assertEqual(collected_data["open_issues"], self.open_issues)
        self.assertEqual(collected_data["vulnerabilities"], self.vulnerabilities)

        analytics_result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(collected_data)

        self.assertEqual(analytics_result["repo_id"], self.repo_id)
        self.assertEqual(analytics_result["metrics_summary"]["commit_count"], self.commit_count)
        self.assertEqual(analytics_result["metrics_summary"]["open_issues"], self.open_issues)
        self.assertEqual(analytics_result["metrics_summary"]["vulnerabilities"], self.vulnerabilities)

        expected_score = max(0.0, 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0))
        self.assertEqual(analytics_result["aggregated_score"], expected_score)

        self.assertTrue(os.path.exists(analytics_result["report_file_path"]))

        with open(analytics_result["report_file_path"], "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["repo_id"], self.repo_id)
        self.assertEqual(file_content["aggregated_score"], expected_score)
        self.assertEqual(file_content["metrics_summary"]["open_issues"], self.open_issues)

        aggregator_instance = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        batch_result = aggregator_instance.aggregate_batch([self.repo_id])
        self.assertIsInstance(batch_result, list)
        self.assertTrue(len(batch_result) > 0)
        self.assertEqual(batch_result[0]["repo_id"], self.repo_id)

if __name__ == "__main__":
    unittest.main()