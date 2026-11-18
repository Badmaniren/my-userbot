import unittest
from unittest.mock import patch
import json
import datetime
import io
import os
import random
import uuid
from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)

class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()
        self.random_repo_id = f"repo_{uuid.uuid4().hex[:8]}"
        self.random_file_path = f"stream_{uuid.uuid4().hex[:8]}.json"

    def tearDown(self):
        if os.path.exists(self.random_file_path):
            try:
                os.remove(self.random_file_path)
            except OSError:
                pass
        
        report_path = f"report_{self.random_repo_id}.json"
        if os.path.exists(report_path):
            try:
                os.remove(report_path)
            except OSError:
                pass

    def test_aggregate_success(self):
        mock_commits = random.randint(10, 500)
        mock_issues = random.randint(0, 10)
        mock_vulnerabilities = random.randint(0, 5)
        mock_status = random.choice(["healthy", "warning", "critical"])

        raw_data = {
            "repo_id": self.random_repo_id,
            "commits": mock_commits,
            "issues": mock_issues,
            "vulnerabilities": mock_vulnerabilities,
            "status": mock_status
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=raw_data) as mock_fetch:
            result = self.aggregator.aggregate(self.random_repo_id)
            mock_fetch.assert_called_once_with(self.random_repo_id)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["metrics"]["commits"], mock_commits)
        self.assertEqual(result["metrics"]["issues"], mock_issues)
        self.assertEqual(result["metrics"]["vulnerabilities"], mock_vulnerabilities)
        self.assertEqual(result["metrics"]["status"], mock_status)
        self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream_success(self):
        nested_data = {
            "stream_id": uuid.uuid4().hex,
            "repo_id": self.random_repo_id,
            "payload": {
                "metrics": {
                    "commits": random.randint(1, 100)
                }
            }
        }
        json_bytes = json.dumps(nested_data).encode("utf-8")

        with patch("builtins.open", return_value=io.BytesIO(json_bytes)) as mock_open:
            result = self.aggregator.aggregate_from_stream(self.random_file_path)
            mock_open.assert_called_once_with(self.random_file_path, 'rb')

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["payload"]["metrics"]["commits"], nested_data["payload"]["metrics"]["commits"])

    def test_calculate_health_score_logic(self):
        commits = random.randint(50, 150)
        issues = random.randint(1, 5)
        vulnerabilities = random.randint(0, 2)

        metrics = {
            "commits": commits,
            "issues": issues,
            "vulnerabilities": vulnerabilities
        }

        expected_score = 100.0 - (issues * 2.0) - (vulnerabilities * 10.0) + (min(commits, 100) * 0.1)
        score = self.aggregator._calculate_health_score(metrics)
        self.assertAlmostEqual(score, expected_score)

    def test_calculate_health_score_bounds_min(self):
        metrics = {
            "commits": 0,
            "issues": 100,
            "vulnerabilities": 50
        }
        score = self.aggregator._calculate_health_score(metrics)
        self.assertEqual(score, 0.0)

    def test_calculate_health_score_bounds_max(self):
        metrics = {
            "commits": 1000,
            "issues": 0,
            "vulnerabilities": 0
        }
        score = self.aggregator._calculate_health_score(metrics)
        self.assertEqual(score, 100.0)

    def test_aggregate_batch_success(self):
        repo_ids = [f"repo_{uuid.uuid4().hex[:6]}" for _ in range(3)]
        mock_return_values = {}
        for rid in repo_ids:
            mock_return_values[rid] = {
                "repo_id": rid,
                "commits": random.randint(1, 50),
                "issues": random.randint(0, 5),
                "vulnerabilities": 0
            }

        def side_effect(r_id):
            return mock_return_values.get(r_id, {})

        with patch("skills.repo_health_collector.fetch_raw_metrics", side_effect=side_effect) as mock_fetch:
            results = self.aggregator.aggregate_batch(repo_ids)
            self.assertEqual(mock_fetch.call_count, len(repo_ids))

        self.assertEqual(len(results), len(repo_ids))
        for res in results:
            rid = res["repo_id"]
            self.assertIn(rid, repo_ids)
            self.assertEqual(res["metrics"]["commits"], mock_return_values[rid]["commits"])

    def test_aggregate_repo_health_analytics_writes_file(self):
        commit_count = random.randint(10, 200)
        open_issues = random.randint(0, 5)
        vulnerabilities = random.randint(0, 3)

        raw_data = {
            "repo_id": self.random_repo_id,
            "commit_count": commit_count,
            "open_issues": open_issues,
            "vulnerabilities": vulnerabilities
        }

        result = aggregate_repo_health_analytics(raw_data)

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertIn("report_file_path", result)
        self.assertTrue(os.path.exists(result["report_file_path"]))

        with open(result["report_file_path"], "r", encoding="utf-8") as f:
            file_content = json.load(f)

        self.assertEqual(file_content["repo_id"], self.random_repo_id)
        self.assertEqual(file_content["metrics_summary"]["commit_count"], commit_count)
        self.assertEqual(file_content["metrics_summary"]["open_issues"], open_issues)
        self.assertEqual(file_content["metrics_summary"]["vulnerabilities"], vulnerabilities)

    def test_collect_repo_health_structure(self):
        commit_count = random.randint(5, 50)
        open_issues = random.randint(0, 3)
        vulnerabilities = random.randint(0, 1)

        data = collect_repo_health(
            repo_id=self.random_repo_id,
            commit_count=commit_count,
            open_issues=open_issues,
            vulnerabilities=vulnerabilities
        )

        self.assertEqual(data["repo_id"], self.random_repo_id)
        self.assertEqual(data["commit_count"], commit_count)
        self.assertEqual(data["open_issues"], open_issues)
        self.assertEqual(data["vulnerabilities"], vulnerabilities)

if __name__ == "__main__":
    unittest.main()