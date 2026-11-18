import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import io
import os
import datetime

from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)


class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def test_calculate_health_score(self):
        aggregator = RepoHealthAnalyticsAggregator()
        for _ in range(10):
            commits = random.randint(0, 500)
            issues = random.randint(0, 10)
            vulnerabilities = random.randint(0, 5)

            metrics = {
                "commits": commits,
                "issues": issues,
                "vulnerabilities": vulnerabilities
            }

            expected_score = max(0.0, 100.0 - (issues * 2.0) - (vulnerabilities * 10.0))
            score = aggregator._calculate_health_score(metrics)
            self.assertEqual(score, expected_score)

    def test_calculate_health_score_zero_floor(self):
        aggregator = RepoHealthAnalyticsAggregator()
        metrics = {
            "commits": random.randint(0, 10),
            "issues": 100,
            "vulnerabilities": 50
        }
        score = aggregator._calculate_health_score(metrics)
        self.assertEqual(score, 0.0)

    def test_aggregate_success(self):
        repo_id = uuid.uuid4().hex
        commits = random.randint(1, 100)
        issues = random.randint(0, 5)
        vulnerabilities = random.randint(0, 2)
        status = random.choice(["active", "stable", "warning"])

        raw_mock_data = {
            "commits": commits,
            "issues": issues,
            "vulnerabilities": vulnerabilities,
            "status": status
        }

        aggregator = RepoHealthAnalyticsAggregator()

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=raw_mock_data) as mock_fetch:
            result = aggregator.aggregate(repo_id)
            mock_fetch.assert_called_once_with(repo_id)

            self.assertEqual(result["repo_id"], repo_id)
            self.assertIn("aggregated_at", result)
            self.assertEqual(result["metrics"]["commits"], commits)
            self.assertEqual(result["metrics"]["issues"], issues)
            self.assertEqual(result["metrics"]["vulnerabilities"], vulnerabilities)
            self.assertEqual(result["metrics"]["status"], status)

    def test_aggregate_fallback_empty(self):
        repo_id = uuid.uuid4().hex
        aggregator = RepoHealthAnalyticsAggregator()

        with patch("skills.repo_health_collector.fetch_raw_metrics", side_effect=AttributeError):
            result = aggregator.aggregate(repo_id)
            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(result["metrics"]["commits"], 0)
            self.assertEqual(result["metrics"]["issues"], 0)
            self.assertEqual(result["metrics"]["vulnerabilities"], 0)
            self.assertEqual(result["metrics"]["status"], "unknown")

    def test_aggregate_from_stream(self):
        repo_id = uuid.uuid4().hex
        file_path = f"{uuid.uuid4().hex}.json"
        file_content = json.dumps({"repo_id": repo_id})

        aggregator = RepoHealthAnalyticsAggregator()

        with patch("builtins.open", mock_open(read_data=file_content)), \
             patch("skills.repo_health_collector.fetch_raw_metrics", return_value={"commits": 5}) as mock_fetch:
            
            result = aggregator.aggregate_from_stream(file_path)
            mock_fetch.assert_called_once_with(repo_id)
            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(result["metrics"]["commits"], 5)

    def test_aggregate_from_stream_empty_repo_id(self):
        file_path = f"{uuid.uuid4().hex}.json"
        file_content = json.dumps({"repo_id": ""})

        aggregator = RepoHealthAnalyticsAggregator()

        with patch("builtins.open", mock_open(read_data=file_content)):
            result = aggregator.aggregate_from_stream(file_path)
            self.assertEqual(result["repo_id"], "")
            self.assertEqual(result["metrics"], {})
            self.assertIn("aggregated_at", result)

    def test_aggregate_repo_health_analytics(self):
        repo_id = uuid.uuid4().hex
        commit_count = random.randint(10, 200)
        open_issues = random.randint(1, 5)
        vulnerabilities = random.randint(0, 1)

        collected_data = {
            "repo_id": repo_id,
            "commit_count": commit_count,
            "open_issues": open_issues,
            "vulnerabilities": vulnerabilities
        }

        expected_score = 100.0 - (open_issues * 2.0) - (vulnerabilities * 10.0)
        expected_filename = f"report_{repo_id}.json"

        m_open = mock_open()
        with patch("builtins.open", m_open):
            result = aggregate_repo_health_analytics(collected_data)

            m_open.assert_called_once_with(expected_filename, "w", encoding="utf-8")
            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(result["aggregated_score"], expected_score)
            self.assertEqual(result["metrics_summary"]["commit_count"], commit_count)
            self.assertEqual(result["metrics_summary"]["open_issues"], open_issues)
            self.assertEqual(result["metrics_summary"]["vulnerabilities"], vulnerabilities)
            self.assertIn("aggregated_at", result)

    def test_collect_repo_health_wrapper(self):
        repo_id = uuid.uuid4().hex
        mock_response = {
            "repo_id": repo_id,
            "commit_count": random.randint(5, 50),
            "open_issues": 0,
            "vulnerabilities": 0
        }

        with patch("skills.repo_health_collector.collect_repo_health", return_value=mock_response) as mock_coll:
            res = collect_repo_health(repo_id=repo_id)
            mock_coll.assert_called_once_with(repo_id=repo_id)
            self.assertEqual(res, mock_response)


if __name__ == "__main__":
    unittest.main()