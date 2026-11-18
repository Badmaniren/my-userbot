import unittest
from unittest.mock import patch, MagicMock
import io
import json
import uuid
import random
import os
from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)

class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()
        self.random_repo_id = uuid.uuid4().hex
        self.random_file_path = f"{uuid.uuid4().hex}.json"

    def tearDown(self):
        if os.path.exists(self.random_file_path):
            try:
                os.remove(self.random_file_path)
            except OSError:
                pass

    def test_aggregate_success(self):
        mock_commits = random.randint(1, 500)
        mock_issues = random.randint(0, 10)
        mock_vulnerabilities = random.randint(0, 5)

        with patch('skills.repo_health_analytics_aggregator.repo_health_collector') as mock_collector:
            mock_collector.fetch_raw_metrics.return_value = {
                "repo_id": self.random_repo_id,
                "commits": mock_commits,
                "issues": mock_issues,
                "vulnerabilities": mock_vulnerabilities,
                "status": "active"
            }

            result = self.aggregator.aggregate(self.random_repo_id)

            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertEqual(result["metrics"]["commits"], mock_commits)
            self.assertEqual(result["metrics"]["issues"], mock_issues)
            self.assertEqual(result["metrics"]["vulnerabilities"], mock_vulnerabilities)
            self.assertEqual(result["metrics"]["status"], "active")
            self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        stream_data = {
            "repo_id": self.random_repo_id,
            "status": "healthy",
            "random_payload": uuid.uuid4().hex
        }
        encoded_data = json.dumps(stream_data).encode('utf-8')

        with patch('skills.repo_health_analytics_aggregator.open', return_value=io.BytesIO(encoded_data), create=True):
            result = self.aggregator.aggregate_from_stream(self.random_file_path)
            self.assertEqual(result["repo_id"], self.random_repo_id)
            self.assertEqual(result["status"], "healthy")
            self.assertEqual(result["random_payload"], stream_data["random_payload"])

    def test_calculate_health_score(self):
        metrics = {
            "commits": random.randint(10, 200),
            "issues": random.randint(1, 5),
            "vulnerabilities": random.randint(0, 2)
        }
        score = self.aggregator._calculate_health_score(metrics)
        self.assertIsInstance(score, float)
        self.assertGreaterEqual(score, 0.0)
        self.assertLessEqual(score, 100.0)

    def test_calculate_health_score_boundaries(self):
        extreme_bad_metrics = {
            "commits": 0,
            "issues": 100,
            "vulnerabilities": 50
        }
        score_bad = self.aggregator._calculate_health_score(extreme_bad_metrics)
        self