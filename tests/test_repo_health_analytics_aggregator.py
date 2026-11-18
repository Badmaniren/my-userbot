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

    def test_aggregate_success(self):
        r_id = str(uuid.uuid4())
        r_commits = random.randint(10, 500)
        r_issues = random.randint(0, 10)
        r_vuln = random.randint(0, 3)
        r_status = random.choice(["active", "stable", "degraded"])

        mock_raw = {
            "repo_id": r_id,
            "commits": r_commits,
            "issues": r_issues,
            "vulnerabilities": r_vuln,
            "status": r_status
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw) as mocked_fetch:
            aggregator = RepoHealthAnalyticsAggregator()
            result = aggregator.aggregate(r_id)

            mocked_fetch.assert_called_once_with(r_id)
            self.assertEqual(result["repo_id"], r_id)
            self.assertEqual(result["metrics"]["commits"], r_commits)
            self.assertEqual(result["metrics"]["issues"], r_issues)
            self.assertEqual(result["metrics"]["vulnerabilities"], r_vuln)
            self.assertEqual(result["metrics"]["status"], r_status)
            self.assertIn("aggregated_at", result)

    def test_aggregate_from_stream(self):
        r_id = str(uuid.uuid4())
        r_val = random.randint(100, 999)
        payload = {
            "repo_id": r_id,
            "random_metric": r_val
        }
        json_data = json.dumps(payload).encode('utf-8')
        mock_file_path = f"{uuid.uuid4().hex}.json"

        with patch("builtins.open", mock_open(read_data=json_data)) as mocked_file:
            aggregator = RepoHealthAnalyticsAggregator()
            result = aggregator.aggregate_from_stream(mock_file_path)

            mocked_file.assert_called_once_with(mock_file_path, 'rb')
            self.assertEqual(result["repo_id"], r_id)
            self.assertEqual(result["random_metric"], r_val)

    def test_calculate_health_score(self):
        aggregator = RepoHealthAnalyticsAggregator()
        
        c = random.randint(0, 50)
        i = random.randint(0, 2)
        v = random.randint(0, 1)

        metrics = {
            "commits": c,
            "issues": i,
            "vulnerabilities": v
        }

        expected = 100.0 - (i * 2.0) - (v * 10.0) + (min(c, 100) * 0.1)
        score = aggregator._calculate_health_score(metrics)
        self.assertAlmostEqual(score, expected)

    def test_calculate_health_score_bounds(self):
        aggregator = RepoHealthAnalyticsAggregator()

        metrics_min = {
            "commits": 0,
            "issues": 100,
            "vulnerabilities": 100
        }
        self.assertEqual(aggregator._calculate_health_score(metrics_min), 0.0)

        metrics_max = {
            "commits": 5000,
            "issues": 0,
            "vulnerabilities": 0
        }
        self.assertEqual(aggregator._calculate_health_score(metrics_max), 100.0)

    def test_aggregate_batch(self):
        repo_ids = [str(uuid.uuid4()), str(uuid.uuid4())]
        r_commits = random.randint(5, 50)
        r_issues = random.randint(1, 5)
        r_vuln = random.randint(0, 2)

        mock_raw = {
            "commits": r_commits,
            "issues": r_issues,
            "vulnerabilities": r_vuln
        }

        with patch("skills.repo_health_collector.fetch_raw_metrics", return_value=mock_raw) as mocked_fetch:
            aggregator = RepoHealthAnalyticsAggregator()
            results = aggregator.aggregate_batch(repo_ids)

            self.assertEqual(len(results), 2)
            for idx, rid in enumerate(repo_ids):
                self.assertEqual(results[idx]["repo_id"], rid)
                self.assertEqual(results[idx]["metrics"]["commits"], r_commits)
                self.assertEqual(results[idx]["metrics"]["issues"], r_issues)
                self.assertEqual(results[idx]["metrics"]["vulnerabilities"], r_vuln)
            
            self.assertEqual(mocked_fetch.call_count, 2)

    def test_aggregate_repo_health_analytics(self):
        r_id = str(uuid.uuid4())
        commits = random.randint(10, 100)
        issues = random.randint(0, 5)
        vulnerabilities = random.randint(0, 2)

        raw_data = {
            "repo_id": r_id,
            "commit_count": commits,
            "open_issues": issues,
            "vulnerabilities": vulnerabilities
        }

        m_open = mock_open()
        with patch("builtins.open", m_open):
            with patch("json.dump") as mocked_json_dump:
                result = aggregate_repo_health_analytics(raw_data)

                self.assertEqual(result["repo_id"], r_id)
                self.assertEqual(result["metrics_summary"]["commit_count"], commits)
                self.assertEqual(result["metrics_summary"]["open_issues"], issues)
                self.assertEqual(result["metrics_summary"]["vulnerabilities"], vulnerabilities)
                self.assertIn("report_file_path", result)
                m_open.assert_called_once_with(f"report_{r_id}.json", "w", encoding="utf-8")
                mocked_json_dump.assert_called_once()

    def test_collect_repo_health(self):
        r_id = str(uuid.uuid4())
        commits = random.randint(1, 100)
        issues = random.randint(0, 10)
        vulnerabilities = random.randint(0, 5)

        res = collect_repo_health(
            repo_id=r_id,
            commit_count=commits,
            open_issues=issues,
            vulnerabilities=vulnerabilities
        )

        self.assertEqual(res["repo_id"], r_id)
        self.assertEqual(res["commit_count"], commits)
        self.assertEqual(res["open_issues"], issues)
        self.assertEqual(res["vulnerabilities"], vulnerabilities)


if __name__ == '__main__':
    unittest.main()