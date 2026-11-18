import unittest
import uuid
import random
import os
import json
from skills import repo_health_analytics_aggregator

class TestRepoHealthAnalyticsAggregatorIntegration(unittest.TestCase):

    def setUp(self):
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.commit_count = random.randint(10, 500)
        self.open_issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 3)
        self.test_stream_file = f"stream_{uuid.uuid4()}.json"

    def tearDown(self):
        report_path = f"report_{self.repo_id}.json"
        if os.path.exists(report_path):
            os.remove(report_path)
        if os.path.exists(self.test_stream_file):
            os.remove(self.test_stream_file)

    def test_collect_and_aggregate_pipeline(self):
        collected_data = repo_health_analytics_aggregator.collect_repo_health(
            repo_id=self.repo_id,
            commit_count=self.commit_count,
            open_issues=self.open_issues,
            vulnerabilities=self.vulnerabilities
        )

        self.assertEqual(collected_data["repo_id"], self.repo_id)
        self.assertEqual(collected_data["commit_count"], self.commit_count)

        result = repo_health_analytics_aggregator.aggregate_repo_health_analytics(collected_data)

        self.assertEqual(result["repo_id"], self.repo_id)
        self.assertIn("aggregated_score", result)
        self.assertIn("report_file_path", result)

        expected_score = 100.0 - (self.open_issues * 2.0) - (self.vulnerabilities * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0

        self.assertEqual(result["aggregated_score"], expected_score)

        report_path = result["report_file_path"]
        self.assertTrue(os.path.exists(report_path))

        with open(report_path, "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["repo_id"], self.repo_id)
        self.assertEqual(file_content["aggregated_score"], expected_score)
        self.assertEqual(file_content["metrics_summary"]["commit_count"], self.commit_count)

    def test_aggregator_class_methods(self):
        aggregator = repo_health_analytics_aggregator.RepoHealthAnalyticsAggregator()

        batch_ids = [f"repo-{uuid.uuid4()}", f"repo-{uuid.uuid4()}"]
        batch_results = aggregator.aggregate_batch(batch_ids)
        self.assertEqual(len(batch_results), 2)
        self.assertEqual(batch_results[0]["repo_id"], batch_ids[0])
        self.assertEqual(batch_results[1]["repo_id"], batch_ids[1])

        stream_data = {
            "repo_id": self.repo_id,
            "random_metric": random.randint(100, 999)
        }
        with open(self.test_stream_file, "w", encoding="utf-8") as f:
            json.dump(stream_data, f)

        stream_result = aggregator.aggregate_from_stream(self.test_stream_file)
        self.assertEqual(stream_result["repo_id"], self.repo_id)
        self.assertEqual(stream_result["random_metric"], stream_data["random_metric"])

        metrics = {
            "commits": self.commit_count,
            "issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities
        }
        score = aggregator._calculate_health_score(metrics)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

if __name__ == "__main__":
    unittest.main()