import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import io

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

    def test_calculate_health_score_standard(self):
        issues_count = random.randint(1, 5)
        vuln_count = random.randint(1, 3)
        commits_count = random.randint(10, 100)

        metrics = {
            "commits": commits_count,
            "issues": issues_count,
            "vulnerabilities": vuln_count
        }

        expected_score = float(100.0 - (issues_count * 2.0) - (vuln_count * 10.0))
        actual_score = self.aggregator._calculate_health_score(metrics)

        self.assertEqual(actual_score, expected_score)

    def test_calculate_health_score_floor_at_zero(self):
        issues_count = random.randint(50, 100)
        vuln_count = random.randint(20, 50)
        commits_count = random.randint(0, 5)

        metrics = {
            "commits": commits_count,
            "issues": issues_count,
            "vulnerabilities": vuln_count
        }

        actual_score = self.aggregator._calculate_health_score(metrics)
        self.assertEqual(actual_score, 0.0)

    def test_aggregate_success(self):
        mock_commits = random.randint(5, 50)
        mock_issues = random.randint(0, 10)
        mock_vulns = random.randint(0, 5)
        mock_status = random.choice(["active", "degraded", "healthy"])

        mock_raw_data = {
            "commits": mock_commits,
            "issues": mock_issues,
            "vulnerabilities": mock_vulns,
            "status": mock_status
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw_data) as mock_fetch:
            result = self.aggregator.aggregate(self.random_repo_id)

            mock_fetch.assert_called_once_with(self.random_repo_id)
            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertIn("aggregated_at", result)
            self.assertEqual(result["metrics"]["commits"], mock_commits)
            self.assertEqual(result["metrics"]["issues"], mock_issues)
            self.assertEqual(result["metrics"]["vulnerabilities"], mock_vulns)
            self.assertEqual(result["metrics"]["status"], mock_status)

    def test_aggregate_from_stream_valid_file(self):
        file_content = json.dumps({"repo_id": self.random_repo_id})
        mock_file_obj = mock_open(read_data=file_content)

        mock_raw_data = {
            "commits": random.randint(1, 10),
            "issues": 0,
            "vulnerabilities": 0,
            "status": "ok"
        }

        with patch("builtins.open", mock_file_obj):
            with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw_data):
                result = self.aggregator.aggregate_from_stream(self.random_file_path)

                self.assertEqual(result["repo_id"], self.random_repo_id)
                self.assertIn("metrics", result)

    def test_aggregate_from_stream_empty_repo_id(self):
        file_content = json.dumps({"repo_id": ""})
        mock_file_obj = mock_open(read_data=file_content)

        with patch("builtins.open", mock_file_obj):
            result = self.aggregator.aggregate_from_stream(self.random_file_path)

            self.assertEqual(result["repo_id"], "")
            self.assertEqual(result["metrics"], {})
            self.assertIn("aggregated_at", result)

    def test_aggregate_repo_health_analytics_function(self):
        commit_val = random.randint(1, 50)
        issue_val = random.randint(1, 5)
        vuln_val = random.randint(0, 2)

        collected_data = {
            "repo_id": self.random_repo_id,
            "commit_count": commit_val,
            "open_issues": issue_val,
            "vulnerabilities": vuln_val
        }

        expected_score = float(100.0 - (issue_val * 2.0) - (vuln_val * 10.0))

        with patch("builtins.open", mock_open()) as mock_file_handler:
            result = aggregate_repo_health_analytics(collected_data)

            mock_file_handler.assert_called_once_with(f"report_{self.random_repo_id}.json", "w", encoding="utf-8")
            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertEqual(result["aggregated_score"], expected_score)
            self.assertEqual(result["metrics_summary"]["commit_count"], commit_val)
            self.assertEqual(result["metrics_summary"]["open_issues"], issue_val)
            self.assertEqual(result["metrics_summary"]["vulnerabilities"], vuln_val)
            self.assertIn("aggregated_at", result)

    def test_collect_repo_health_delegation(self):
        kwargs = {
            "repo_id": self.random_repo_id,
            "commit_count": random.randint(1, 100),
            "open_issues": random.randint(0, 5),
            "vulnerabilities": 0
        }

        if repo_health_collector is not None and hasattr(repo_health_collector, "collect_repo_health"):
            with patch("skills.repo_health_collector.collect_repo_health", return_value=kwargs) as mock_collect:
                res = collect_repo_health(**kwargs)
                mock_collect.assert_called_once_with(**kwargs)
                self.assertEqual(res, kwargs)
        else:
            res = collect_repo_health(**kwargs)
            self.assertIsInstance(res, dict)


if __name__ == "__main__":
    unittest.main()