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
            try:
                os.remove(self.report_file_path)
            except OSError:
                pass

    def test_integration_aggregate_repo_health_analytics(self):
        collected_data = {
            "repo_id": self.repo_id,
            "commit_count": self.commit_count,
            "open_issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities
        }

        result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(collected_data)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertIn("aggregated_score", result)
        self.assertIn("metrics_summary", result)
        self.assertEqual(result["metrics_summary"]["commit_count"], self.commit_count)
        self.assertEqual(result["metrics_summary"]["open_issues"], self.open_issues)
        self.assertEqual(result["metrics_summary"]["vulnerabilities"], self.vulnerabilities)

        expected_score = float(max(0.0, 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)))
        self.assertEqual(result["aggregated_score"], expected_score)

        self.assertTrue(os.path.exists(self.report_file_path))

    def test_integration_aggregator_class_flow(self):
        aggregator = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()
        
        metrics = {
            "commits": self.commit_count,
            "issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities
        }
        score = aggregator._calculate_health_score(metrics)
        expected_score = float(max(0.0, 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)))
        self.assertEqual(score, expected_score)

        stream_data_path = f"stream_{uuid.uuid4()}.json"
        try:
            import json
            with open(stream_data_path, "w", encoding="utf-8") as f:
                json.dump({"repo_id": self.repo_id}, f)

            stream_result = aggregator.aggregate_from_stream(stream_data_path)
            self.assertEqual(stream_result["repo_id"], self.repo_id)
            self.assertIn("metrics", stream_result)
        finally:
            if os.path.exists(stream_data_path):
                os.remove(stream_data_path)

    def test_integration_collect_repo_health_wrapper(self):
        collected = repo_health_analytics_aggregator.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )
        self.assertIsInstance(collected, dict)
        self.assertEqual(collected.get("repo_id"), self.repo_id)

if __name__ == "__main__":
    unittest.main()