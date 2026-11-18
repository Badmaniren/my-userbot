import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import io
import os

from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)


class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def test_calculate_health_score_normal(self):
        aggregator = RepoHealthAnalyticsAggregator()
        issues_count = random.randint(1, 5)
        vuln_count = random.randint(1, 3)
        commit_count = random.randint(10, 100)

        metrics = {
            "commits": commit_count,
            "issues": issues_count,
            "vulnerabilities": vuln_count
        }

        expected_score = float(100.0 - (issues_count * 2.0) - (vuln_count * 10.0))
        calculated_score = aggregator._calculate_health_score(metrics)

        self.assertEqual(calculated_score, expected_score)

    def test_calculate_health_score_floor_zero(self):
        aggregator = RepoHealthAnalyticsAggregator()
        issues_count = random.randint(50, 100)
        vuln_count = random.randint(20, 50)
        
        metrics = {
            "commits": random.randint(0, 5),
            "issues": issues_count,
            "vulnerabilities": vuln_count
        }

        calculated_score = aggregator._calculate_health_score(metrics)
        self.assertEqual(calculated_score, 0.0)

    def test_aggregate_method_success(self):
        repo_id = uuid.uuid4().hex
        commits_val = random.randint(5, 50)
        issues_val = random.randint(0, 10)
        vuln_val = random.randint(0, 5)
        status_val = uuid.uuid4().hex[:8]

        mock_raw_data = {
            "commits": commits_val,
            "issues": issues_val,
            "vulnerabilities": vuln_val,
            "status": status_val
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw_data) as mock_fetch:
            aggregator = RepoHealthAnalyticsAggregator()
            result = aggregator.aggregate(repo_id)

            mock_fetch.assert_called_once_with(repo_id)
            self.assertEqual(result["repo_id"], repo_id)
            self.assertIn("aggregated_at", result)
            self.assertEqual(result["metrics"]["commits"], commits_val)
            self.assertEqual(result["metrics"]["issues"], issues_val)
            self.assertEqual(result["metrics"]["vulnerabilities"], vuln_val)
            self.assertEqual(result["metrics"]["status"], status_val)

    def test_aggregate_from_stream_valid_file(self):
        file_path = f"{uuid.uuid4().hex}.json"
        repo_id = uuid.uuid4().hex
        file_content = json.dumps({"repo_id": repo_id})

        mock_file = mock_open(read_data=file_content)

        with patch("builtins.open", mock_file):
            with patch("skills.repo_health_collector.fetch_raw_metrics", return_value={}) as mock_fetch:
                aggregator = RepoHealthAnalyticsAggregator()
                result = aggregator.aggregate_from_stream(file_path)

                mock_fetch.assert_called_once_with(repo_id)
                self.assertEqual(result["repo_id"], repo_id)
                self.assertIn("metrics", result)
                self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream_empty_repo_id(self):
        file_path = f"{uuid.uuid4().hex}.json"
        file_content = json.dumps({"other_field": uuid.uuid4().hex})

        mock_file = mock_open(read_data=file_content)

        with patch("builtins.open", mock_file):
            aggregator = RepoHealthAnalyticsAggregator()
            result = aggregator.aggregate_from_stream(file_path)

            self.assertEqual(result["repo_id"], "")
            self.assertEqual(result["metrics"], {})
            self.assertIn("aggregated_at", result)

    def test_aggregate_repo_health_analytics_function(self):
        repo_id = uuid.uuid4().hex
        commit_count = random.randint(10, 100)
        open_issues = random.randint(0, 10)
        vulnerabilities = random.randint(0, 5)

        collected_data = {
            "repo_id": repo_id,
            "commit_count": commit_count,
            "open_issues": open_issues,
            "vulnerabilities": vulnerabilities
        }

        expected_score = float(100.0 - (open_issues * 2.0) - (vulnerabilities * 10.0))
        expected_filename = f"report_{repo_id}.json"

        mock_file_handler = mock_open()

        with patch("builtins.open", mock_file_handler) as mocked_open:
            result = aggregate_repo_health_analytics(collected_data)

            mocked_open.assert_called_with(expected_filename, "w", encoding="utf-8")
            self.assertEqual(result["repo_id"], repo_id)
            self.assertEqual(result["aggregated_score"], expected_score)
            self.assertEqual(result["metrics_summary"]["commit_count"], commit_count)
            self.assertEqual(result["metrics_summary"]["open_issues"], open_issues)
            self.assertEqual(result["metrics_summary"]["vulnerabilities"], vulnerabilities)
            self.assertIn("aggregated_at", result)

    def test_collect_repo_health_delegation(self):
        repo_id = uuid.uuid4().hex
        expected_result = {
            "repo_id": repo_id