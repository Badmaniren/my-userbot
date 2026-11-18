import unittest
from unittest.mock import patch, mock_open
import io
import json
import datetime
import uuid
import random

from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health,
    repo_health_collector
)


class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()
        self.random_repo_id = uuid.uuid4().hex
        self.random_file_path = f"{uuid.uuid4().hex}.json"

    def test_aggregate_success(self):
        mock_raw_data = {
            "repo_id": self.random_repo_id,
            "commits": random.randint(1, 500),
            "issues": random.randint(0, 10),
            "vulnerabilities": random.randint(0, 5),
            "status": random.choice(["active", "stable", "warning"])
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw_data) as mock_fetch:
            result = self.aggregator.aggregate(self.random_repo_id)

            mock_fetch.assert_called_once_with(self.random_repo_id)
            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertEqual(result["metrics"]["commits"], mock_raw_data["commits"])
            self.assertEqual(result["metrics"]["issues"], mock_raw_data["issues"])
            self.assertEqual(result["metrics"]["vulnerabilities"], mock_raw_data["vulnerabilities"])
            self.assertEqual(result["metrics"]["status"], mock_raw_data["status"])
            self.assertIn("aggregated_at", result)

    def test_aggregate_fallback_empty(self):
        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value={}) as mock_fetch:
            result = self.aggregator.aggregate(self.random_repo_id)

            mock_fetch.assert_called_once_with(self.random_repo_id)
            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertEqual(result["metrics"]["commits"], 0)
            self.assertEqual(result["metrics"]["issues"], 0)
            self.assertEqual(result["metrics"]["vulnerabilities"], 0)
            self.assertEqual(result["metrics"]["status"], "unknown")
            self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        expected_data = {
            "repo_id": self.random_repo_id,
            "stream_marker": uuid.uuid4().hex,
            "timestamp": datetime.datetime.utcnow().isoformat()
        }
        json_bytes = json.dumps(expected_data).encode("utf-8")

        with patch("builtins.open", mock_open(read_data=json_bytes)) as mock_file:
            result = self.aggregator.aggregate_from_stream(self.random_file_path)

            mock_file.assert_called_once_with(self.random_file_path, 'rb')
            self.assertEqual(result, expected_data)

    def test_calculate_health_score(self):
        commits = random.randint(50, 150)
        issues = random.randint(1, 5)
        vulnerabilities = random.randint(1, 2)

        metrics = {
            "commits": commits,
            "issues": issues,
            "vulnerabilities": vulnerabilities
        }

        expected_score = 100.0 - (issues * 2.0) - (vulnerabilities * 10.0) + (min(commits, 100) * 0.1)
        score = self.aggregator._calculate_health_score(metrics)

        self.assertAlmostEqual(score, expected_score)

    def test_calculate_health_score_bounds(self):
        metrics_low = {
            "commits": 0,
            "issues": 100,
            "vulnerabilities": 100
        }
        self.assertEqual(self.aggregator._calculate_health_score(metrics_low), 0.0)

        metrics_high = {
            "commits": 10000,
            "issues": 0,
            "vulnerabilities": 0
        }
        self.assertEqual(self.aggregator._calculate_health_score(metrics_high), 100.0)

    def test_aggregate_batch(self):
        repo_ids = [uuid.uuid4().hex for _ in range(3)]
        
        def mock_fetch_side_effect(rid):
            return {
                "repo_id": rid,
                "commits": len(rid),
                "issues": 1,
                "vulnerabilities": 0
            }

        with patch("skills.repo_health_collector.fetch_raw_metrics", side_effect=mock_fetch_side_effect) as mock_fetch:
            results = self.aggregator.aggregate_batch(repo_ids)

            self.assertEqual(len(results), len(repo_ids))
            for i, res in enumerate(results):
                self.assertEqual(res["repo_id"], repo_ids[i])
                self.assertEqual(res["metrics"]["commits"], len(repo_ids[i]))
                self.assertEqual(res["metrics"]["issues"], 1)
                self.assertEqual(res["metrics"]["vulnerabilities"], 0)
            self.assertEqual(mock_fetch.call_count, len(repo_ids))

    def test_aggregate_repo_health_analytics(self):
        commit_count = random.randint(10, 200)
        open_issues = random.randint(0, 5)
        vulnerabilities = random.randint(0, 2)

        raw_data = {
            "repo_id": self.random_repo_id,
            "commit_count": commit_count,
            "open_issues": open_issues,
            "vulnerabilities": vulnerabilities
        }

        expected_score = max(0.0, 100.0 - (open_issues * 2.0) - (vulnerabilities * 10.0))
        expected_path = f"report_{self.random_repo_id}.json"

        with patch("builtins.open", mock_open()) as mock_file:
            with patch("json.dump") as mock_json_dump:
                result = aggregate_repo_health_analytics(raw_data)

                mock_file.assert_called_once_with(expected_path, "w", encoding="utf-8")
                mock_json_dump.assert_called_once()
                self.assertEqual(result["repo_id"], self.random_repo_id)
                self.assertEqual(result["aggregated_score"], expected_score)
                self.assertEqual(result["metrics_summary"]["commit_count"], commit_count)
                self.assertEqual(result["metrics_summary"]["open_issues"], open_issues)
                self.assertEqual(result["metrics_summary"]["vulnerabilities"], vulnerabilities)
                self.assertEqual(result["report_file_path"], expected_path)

    def test_collect_repo_health(self):
        commit_count = random.randint(0, 100)
        open_issues = random.randint(0, 10)
        vulnerabilities = random.randint(0, 5)

        result = collect_repo_health(
            self.random_repo_id,
            commit_count=commit_count,
            open_issues=open_issues,
            vulnerabilities=vulnerabilities
        )

        self.assertEqual(result["repo_id"], self.random_repo_id)
        self.assertEqual(result["commit_count"], commit_count)
        self.assertEqual(result["open_issues"], open_issues)
        self.assertEqual(result["vulnerabilities"], vulnerabilities)


if __name__ == '__main__':
    unittest.main()