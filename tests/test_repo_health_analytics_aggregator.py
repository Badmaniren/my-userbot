import unittest
from unittest.mock import patch
import io
import json
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
        self.repo_id = uuid.uuid4().hex
        self.commit_count = random.randint(1, 500)
        self.open_issues = random.randint(0, 10)
        self.vulnerabilities = random.randint(0, 5)
        self.status = random.choice(["active", "degraded", "critical", "healthy"])

    def test_aggregate_with_collector(self):
        mock_raw_metrics = {
            "repo_id": self.repo_id,
            "commits": self.commit_count,
            "issues": self.open_issues,
            "vulnerabilities": self.vulnerabilities,
            "status": self.status
        }
        with patch("skills.repo_health_analytics_aggregator.repo_health_collector") as mock_collector:
            mock_collector.fetch_raw_metrics.return_value = mock_raw_metrics
            result = self.aggregator.aggregate(self.repo_id)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["metrics"]["commits"], self.commit_count)
            self.assertEqual(result["metrics"]["issues"], self.open_issues)
            self.assertEqual(result["metrics"]["vulnerabilities"], self.vulnerabilities)
            self.assertEqual(result["metrics"]["status"], self.status)
            self.assertIn("aggregated_at", result)

    def test_aggregate_without_collector(self):
        with patch("skills.repo_health_analytics_aggregator.repo_health_collector", None):
            result = self.aggregator.aggregate(self.repo_id)

            self.assertEqual(result["repo_id"], self.repo_id)
            self.assertEqual(result["metrics"]["commits"], 0)
            self.assertEqual(result["metrics"]["issues"], 0)
            self.assertEqual(result["metrics"]["vulnerabilities"], 0)
            self.assertEqual(result["metrics"]["status"], "unknown")
            self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        stream_data = {
            "repo_id": self.repo_id,
            "status": self.status,
            "random_metric": random.randint(100, 999)
        }
        encoded_data = json.dumps(stream_data).encode("utf-8")
        random_file_path = f"stream_{uuid.uuid4().hex}.json"

        with patch("builtins.open", return