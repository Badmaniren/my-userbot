import unittest
from unittest.mock import patch, MagicMock
import json
import io
import os
import uuid
import random
from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)

class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()
        self.repo_id = uuid.uuid4().hex
        self.commits = random.randint(10, 500)
        self.issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 5)
        self.status = random.choice(["active", "stable", "critical", "unknown"])

    def test_aggregate_success(self):
        mock_raw_metrics = {
            "repo_id": self.repo_id,
            "commits": self.commits,
            "issues": self.issues,
            "vulnerabilities": self.vulnerabilities,
            "status": self.status
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw_metrics) as mock_fetch:
            result = self.aggregator.aggregate(self.repo_id)
            mock_fetch.assert_called_once_with(self.repo_id)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["metrics"]["commits"], self.commits)
            self.assertEqual(result["metrics"]["issues"], self.issues)
            self.assertEqual(result["metrics"]["vulnerabilities"], self.vulnerabilities)
            self.assertEqual(result["metrics"]["status"], self.status)
            self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        file_path = f"test_stream_{uuid.uuid4().hex}.json"
        stream_data = {
            "repo_id": self.repo_id,
            "custom_payload": uuid.uuid4().hex,
            "metrics": {
                "commits": self.commits
            }
        }
        encoded_data = json.dumps(stream_data).encode('utf-8')

        with patch("builtins.open", unittest.mock.mock_open(read_data=encoded_data)) as mock_file:
            result = self.aggregator.aggregate_from_stream(file_path)
            mock_file.assert_called_once_with(file_path, 'rb')
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["metrics"]["commits"], self.commits)

    def test_calculate_health_score(self):
        metrics = {
            "commits": 50,
            "issues": 2,
            "vulnerabilities": 1
        }
        score = self.aggregator._calculate_health_score(metrics)
        expected = 100.0 - (2 * 2.0) - (1 * 10.0) + (50 * 0.1)
        self.assertEqual(score, expected)

    def test_calculate_health_score_clamping_low(self):
        metrics = {
            "commits": 0,
            "issues": 100,
            "vulnerabilities": 100
        }
        score = self.aggregator._calculate_health_score(metrics)
        self.assertEqual(score, 0.0)

    def test_calculate_health_score_clamping_high(self):
        metrics = {
            "commits": 10000,
            "issues": 0,
            "vulnerabilities": 0
        }
        score = self.aggregator._calculate_health_score(metrics)
        self.assertEqual(score, 100.0)

    def test_aggregate_batch(self):
        repo_ids = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_returns = [
            {"commits": 10, "issues": 1, "vulnerabilities": 0},
            {"commits": 20, "issues": 0, "vulnerabilities": 1}
        ]

        with patch("skills.repo_health_collector.fetch_raw_metrics", side_effect=mock_returns) as mock_fetch:
            results = self.aggregator.aggregate_batch(repo_ids)
            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["repo_id"], repo_ids[0])
            self.assertEqual(results[0]["metrics"]["commits"], 10)
            self.assertEqual(results[1]["repo_id"], repo_ids[1])
            self.assertEqual(results[1]["metrics"]["vulnerabilities"], 1)
            self.assertEqual(mock_fetch.call_count, 2)

    def test_aggregate_repo_health_analytics(self):
        raw_data = {
            "repo_id": self.repo_id,
            "commit_count": self.commits,
            "open_issues": self.issues,
            "vulnerabilities": self.vulnerabilities
        }

        mock_file_open = unittest.mock.mock_open()
        with patch("builtins.open", mock_file_open):
            result = aggregate_repo_health_analytics(raw_data)
            
            mock_file_open.assert_called_once_with(f"report_{self.repo_id}.json", "w", encoding="utf-8")
            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertIn("aggregated_score", result)
            self.assertIn("report_file_path", result)
            self.assertEqual(result["metrics_summary"]["commit_count"], self.commits)

    def test_collect_repo_health(self):
        res = collect_repo_health(self.repo_id, self.commits, self.issues, self.vulnerabilities)
        self.assertEqual(res["repo_id"], self.repo_id)
        self.assertEqual(res["commit_count"], self.commits)
        self.assertEqual(res["open_issues"], self.issues)
        self.assertEqual(res["vulnerabilities"], self.vulnerabilities)