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

    def test_integration_flow_without_mocks(self):
        collected_data = repo_health_collector.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )

        self.assertEqual(collected_data["repo_id"], self.repo_id)
        self.assertEqual(collected_data["commit_count"], self.commit_count)

        aggregated_result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(collected_data)

        self.assertEqual(aggregated_result["repo_id"], self.repo_id)
        self.assertIn("aggregated_score", aggregated_result)
        self.assertIn("metrics_summary", aggregated_result)
        
        expected_score = 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0
            
        self.assertEqual(aggregated_result["aggregated_score"], expected_score)
        self.assertEqual(aggregated_result["metrics_summary"]["commit_count"], self.commit_count)
        self.assertEqual(aggregated_result["metrics_summary"]["open_issues"], self.open_issues)
        self.assertEqual(aggregated_result["metrics_summary"]["vulnerabilities"], self.vulnerabilities)

        self.assertTrue(os.path.exists(self.report_file_path), "Файл отчета должен быть создан на диске")

        with open(self.report_file_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["repo_id"], self.repo_id)
        self.assertEqual(file_content["aggregated_score"], expected_score)
        self.assertEqual(file_content["metrics_summary"]["open_issues"], self.open_issues)

        aggregator_instance = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        calculated_score = aggregator_instance._calculate_health_score({
            "commits": self.commit_count,
            "issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities
        })
        self.assertIsInstance(calculated_score, float)

if __name__ == "__main__":
    unittest.main()