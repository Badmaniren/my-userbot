import unittest
import uuid
import random
import os
from skills.repo_health_collector import collect_repo_health
from skills.repo_health_analytics_aggregator import aggregate_repo_health_analytics

class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):
    def test_aggregate_repo_health_analytics_integration(self):
        test_repo_id = f"repo-{uuid.uuid4()}"
        random_commit_count = random.randint(10, 500)
        random_open_issues = random.randint(0, 50)
        random_vulnerabilities = random.randint(0, 10)

        raw_data = collect_repo_health(
            repo_id=test_repo_id,
            commit_count=random_commit_count,
            open_issues=random_open_issues,
            vulnerabilities=random_vulnerabilities
        )

        self.assertIsNotNone(raw_data)
        self.assertEqual(raw_data.get("repo_id"), test_repo_id)

        aggregated_report = aggregate_repo_health_analytics(raw_data)

        self.assertIsNotNone(aggregated_report)
        self.assertEqual(aggregated_report.get("repo_id"), test_repo_id)
        self.assertIn("aggregated_score", aggregated_report)
        self.assertIn("metrics_summary", aggregated_report)
        
        self.assertEqual(
            aggregated_report["metrics_summary"]["commit_count"], 
            random_commit_count
        )
        self.assertEqual(
            aggregated_report["metrics_summary"]["open_issues"], 
            random_open_issues
        )
        self.assertEqual(
            aggregated_report["metrics_summary"]["vulnerabilities"], 
            random_vulnerabilities
        )

        report_file_path = aggregated_report.get("report_file_path")
        if report_file_path:
            self.assertTrue(os.path.exists(report_file_path))
            if os.path.exists(report_file_path):
                os.remove(report_file_path)

if __name__ == "__main__":
    unittest.main()