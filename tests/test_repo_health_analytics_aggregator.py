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
    collect_repo_health
)


class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def test_aggregate_success(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(1, 500)
        i_count = random.randint(0, 10)
        v_count = random.randint(0, 5)
        st = uuid.uuid4().hex

        raw_data = {
            "repo_id": r_id,
            "commits": c_count,
            "issues": i_count,
            "vulnerabilities": v_count,
            "status": st
        }

        aggregator = RepoHealthAnalyticsAggregator()
        with patch("skills.repo_health_analytics_aggregator.repo_health_collector") as mock_collector:
            mock_collector.fetch_raw_metrics.return_value = raw_data
            result = aggregator.aggregate(r_id)

        self.assertEqual(result["repo_id"], r_id)
        self.assertEqual(result["metrics"]["commits"], c_count)
        self.assertEqual(result["metrics"]["issues"], i_count)
        self.assertEqual(result["metrics"]["vulnerabilities"], v_count)
        self.assertEqual(result["metrics"]["status"], st)
        self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        r_id = uuid.uuid4().hex
        payload = json.dumps({"repo_id": r_id, "data": uuid.uuid4().hex}).encode("utf-8")
        file_path = f"{uuid.uuid4().hex}.json"

        aggregator = RepoHealthAnalyticsAggregator()
        with patch("builtins.open", mock_open(read_data=payload)):
            result = aggregator.aggregate_from_stream(file_path)

        self.assertEqual(result["repo_id"], r_id)

    def test_calculate_health_score(self):
        aggregator = RepoHealthAnalyticsAggregator()
        
        metrics_good = {"commits": 150, "issues": 0, "vulnerabilities": 0}
        score_good = aggregator._calculate_health_score(metrics_good)
        self.assertAlmostEqual(score_good, 100.0)

        metrics_bad = {"commits": 0, "issues": 10, "vulnerabilities": 10}
        score_bad = aggregator._calculate_health_score(metrics_bad)
        self.assertEqual(score_bad, 0.0)

        metrics_mid = {"commits": 50, "issues": 2, "vulnerabilities": 1}
        score_mid = aggregator._calculate_health_score(metrics_mid)
        expected = 100.0