import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import io
import json
import datetime

from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health,
)


class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def test_aggregate_with_collector(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(1, 500)
        i_count = random.randint(0, 50)
        v_count = random.randint(0, 10)
        status_val = uuid.uuid4().hex

        fake_raw = {
            "repo_id": r_id,
            "commits": c_count,
            "issues": i_count,
            "vulnerabilities": v_count,
            "status": status_val
        }

        aggregator = RepoHealthAnalyticsAggregator()
        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=fake_raw) as mock_fetch:
            result = aggregator.aggregate(r_id)
            mock_fetch.assert_called_once_with(r_id)

        self.assertEqual(result["repo_id"], r_id)
        self.assertEqual(result["metrics"]["commits"], c_count)
        self.assertEqual(result["metrics"]["issues"], i_count)
        self.assertEqual(result["metrics"]["vulnerabilities"], v_count)
        self.assertEqual(result["metrics"]["status"], status_val)
        self.assertIn("aggregated_at", result)

    def test_aggregate_without_collector(self):
        r_id = uuid.uuid4().hex
        aggregator = RepoHealthAnalyticsAggregator()
        with patch("skills.repo_health_analytics_aggregator.repo_health_collector", None):
            result = aggregator.aggregate(r_id)

        self.assertEqual(result["repo_id"], r_id)
        self.assertEqual(result["metrics"]["commits"], 0)
        self.assertEqual(result["metrics"]["issues"], 0)
        self.assertEqual(result["metrics"]["vulnerabilities"], 0)
        self.assertEqual(result["metrics"]["status"], "unknown")
        self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        r_id = uuid.uuid4().hex
        payload = {"repo_id": r_id, "random_key": uuid.uuid4().hex}
        stream_data = json.dumps(payload).encode("utf-8")
        f_path = f"{uuid.uuid4().hex}.json"

        aggregator = RepoHealthAnalyticsAggregator()
        with patch("builtins.open", mock_open(read_data=stream_data)):
            res = aggregator.aggregate_from_stream(f_path)

        self.assertEqual(res["repo_id"], r_id)
        self.assertEqual(res["random_key"], payload["random_key"])

    def test_calculate_health_score(self):
        aggregator = RepoHealthAnalyticsAggregator()
        
        # score = 100 - (issues * 2) - (vols * 10) + (min(commits, 100) * 0.1)
        # Let's test normal bounds
        metrics = {"commits": 50, "issues": 5, "vulnerabilities": 1}
        # 100 - 10 - 10 + 5 = 85.0
        score = aggregator._calculate_health_score(metrics)
        self.assertAlmostEqual(score, 85.0)

        # Test lower bound (negative clamp)
        metrics_low = {"commits": 0, "issues": 100, "vulnerabilities": 10}
        score_low = aggregator._calculate_health_score(metrics_low)
        self.assertEqual(score_low, 0.0)

        # Test upper bound (above 100 clamp)
        metrics_high = {"commits": 500, "issues": 0, "vulnerabilities": 0}
        score_high = aggregator._calculate_health_score(metrics_high)
        self.assertEqual(score_high, 100.0)

    def test_aggregate_batch(self):
        r_ids = [uuid.uuid4().hex, uuid.uuid4().hex]
        aggregator = RepoHealthAnalyticsAggregator()

        def side_effect(rid):
            return {
                "repo_id": rid,
                "commits": len(rid),
                "issues": 1,
                "vulnerabilities": 0
            }

        with patch("skills.repo_health_collector.fetch_raw_metrics", side_effect=side_effect):
            batch_res = aggregator.aggregate_batch(r_ids)

        self.assertEqual(len(batch_res), 2)
        self.assertEqual(batch_res[0]["repo_id"], r_ids[0])
        self.assertEqual(batch_res[0]["metrics"]["commits"], len(r_ids[0]))
        self.assertEqual(batch_res[1]["repo_id"], r_ids[1])
        self.assertEqual(batch_res[1]["metrics"]["commits"], len(r_ids[1]))

    def test_aggregate_repo_health_analytics(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(10, 100)
        i_count = random.randint(0, 5)
        v_count = random.randint(0, 2)

        raw_data = {
            "repo_id": r_id,
            "commit_count": c_count,
            "open_issues": i_count,
            "vulnerabilities": v_count
        }

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            res = aggregate_repo_health_analytics(raw_data)

        self.assertEqual(res["repo_id"], r_id)
        self.assertEqual(res["metrics_summary"]["commit_count"], c_count)
        self.assertEqual(res["metrics_summary"]["open_issues"], i_count)
        self.assertEqual(res["metrics_summary"]["vulnerabilities"], v_count)
        expected_score = max(0.0, 100.0 - (i_count * 2.0) - (v_count * 10.0))
        self.assertEqual(res["aggregated_score"], expected_score)
        self.assertIn("report_file_path", res)
        mock_file.assert_called_once_with(f"report_{r_id}.json", "w", encoding="utf-8")

    def test_collect_repo_health(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(1, 1000)
        i_count = random.randint(0, 100)
        v_count = random.randint(0, 50)

        result = collect_repo_health(r_id, commit_count=c_count, open_issues=i_count, vulnerabilities=v_count)

        self.assertEqual(result["repo_id"], r_id)
        self.assertEqual(result["commit_count"], c_count)
        self.assertEqual(result["open_issues"], i_count)
        self.assertEqual(result["vulnerabilities"], v_count)


if __name__ == "__main__":
    unittest.main()