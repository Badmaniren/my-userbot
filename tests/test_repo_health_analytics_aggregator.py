import unittest
from unittest.mock import patch
import io
import json
import uuid
import random
import string
from skills.repo_health_analytics_aggregator import (
    RepoHealthAnalyticsAggregator,
    aggregate_repo_health_analytics,
    collect_repo_health
)

class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()

    def test_aggregate_with_collector(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(10, 500)
        i_count = random.randint(0, 10)
        v_count = random.randint(0, 5)
        status_val = random.choice(["active", "stable", "critical"])

        mock_metrics = {
            "repo_id": r_id,
            "commits": c_count,
            "issues": i_count,
            "vulnerabilities": v_count,
            "status": status_val
        }

        with patch("skills.repo_health_analytics_aggregator.repo_health_collector") as mock_collector:
            mock_collector.fetch_raw_metrics.return_value = mock_metrics
            result = self.aggregator.aggregate(r_id)

            self.assertEqual(result["repo_id"], r_id)
            self.assertEqual(result["metrics"]["commits"], c_count)
            self.assertEqual(result["metrics"]["issues"], i_count)
            self.assertEqual(result["metrics"]["vulnerabilities"], v_count)
            self.assertEqual(result["metrics"]["status"], status_val)
            self.assertIn("aggregated_at", result)

    def test_aggregate_without_collector(self):
        r_id = uuid.uuid4().hex
        with patch("skills.repo_health_analytics_aggregator.repo_health_collector", None):
            result = self.aggregator.aggregate(r_id)
            self.assertEqual(result["repo_id"], r_id)
            self.assertEqual(result["metrics"]["commits"], 0)
            self.assertEqual(result["metrics"]["issues"], 0)
            self.assertEqual(result["metrics"]["vulnerabilities"], 0)
            self.assertEqual(result["metrics"]["status"], "unknown")

    def test_aggregate_from_stream(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(1, 1000)
        payload = {"repo_id": r_id, "random_val": ''.join(random.choices(string.ascii_letters, k=10))}
        stream_data = json.dumps(payload).encode('utf-8')
        mock_file = io.BytesIO(stream_data)

        random_file_path = f"{uuid.uuid4().hex}.json"
        with patch("builtins.open", return_value=mock_file) as mock_open:
            result = self.aggregator.aggregate_from_stream(random_file_path)
            mock_open.assert_called_once_with(random_file_path, 'rb')
            self.assertEqual(result["repo_id"], r_id)
            self.assertEqual(result["random_val"], payload["random_val"])

    def test_calculate_health_score(self):
        issues = random.randint(0, 5)
        vulnerabilities = random.randint(0, 2)
        commits = random.randint(0, 150)

        metrics = {
            "commits": commits,
            "issues": issues,
            "vulnerabilities": vulnerabilities
        }

        expected_score = 100.0 - (issues * 2.0) - (vulnerabilities * 10.0) + (min(commits, 100) * 0.1)
        if expected_score < 0.0:
            expected_score = 0.0
        elif expected_score > 100.0:
            expected_score = 100.0

        score = self.aggregator._calculate_health_score(metrics)
        self.assertAlmostEqual(score, expected_score)

    def test_calculate_health_score_bounds(self):
        metrics_low = {"commits": 0, "issues": 100, "vulnerabilities": 100}
        self.assertEqual(self.aggregator._calculate_health_score(metrics_low), 0.0)

        metrics_high = {"commits": 1000, "issues": 0, "vulnerabilities": 0}
        self.assertEqual(self.aggregator._calculate_health_score(metrics_high), 100.0)

    def test_aggregate_batch(self):
        repo_ids = [uuid.uuid4().hex, uuid.uuid4().hex]
        mock_returns = {
            repo_ids[0]: {"commits": 12, "issues": 1, "vulnerabilities": 0},
            repo_ids[1]: {"commits": 45, "issues": 3, "vulnerabilities": 1}
        }

        with patch("skills.repo_health_analytics_aggregator.repo_health_collector") as mock_collector:
            mock_collector.fetch_raw_metrics.side_effect = lambda rid: mock_returns[rid]
            results = self.aggregator.aggregate_batch(repo_ids)

            self.assertEqual(len(results), 2)
            self.assertEqual(results[0]["repo_id"], repo_ids[0])
            self.assertEqual(results[0]["metrics"]["commits"], 12)
            self.assertEqual(results[1]["repo_id"], repo_ids[1])
            self.assertEqual(results[1]["metrics"]["vulnerabilities"], 1)

    def test_aggregate_repo_health_analytics(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(5, 50)
        i_count = random.randint(0, 5)
        v_count = random.randint(0, 2)

        raw_data = {
            "repo_id": r_id,
            "commit_count": c_count,
            "open_issues": i_count,
            "vulnerabilities": v_count
        }

        expected_score = 100.0 - (i_count * 2.0) - (v_count * 10.0)
        if expected_score < 0.0:
            expected_score = 0.0

        mock_file = io.StringIO()
        with patch("builtins.open", return_value=mock_file) as mock_open:
            with patch("json.dump") as mock_json_dump:
                result = aggregate_repo_health_analytics(raw_data)

                expected_path = f"report_{r_id}.json"
                mock_open.assert_called_once_with(expected_path, "w", encoding="utf-8")
                self.assertEqual(result["repo_id"], r_id)
                self.assertEqual(result["aggregated_score"], expected_score)
                self.assertEqual(result["metrics_summary"]["commit_count"], c_count)
                self.assertEqual(result["report_file_path"], expected_path)
                mock_json_dump.assert_called_once()

    def test_collect_repo_health(self):
        r_id = uuid.uuid4().hex
        c_count = random.randint(1, 100)
        i_count = random.randint(1, 10)
        v_count = random.randint(0, 5)

        result = collect_repo_health(
            repo_id=r_id,
            commit_count=c_count,
            open_issues=i_count,
            vulnerabilities=v_count
        )

        self.assertEqual(result["repo_id"], r_id)
        self.assertEqual(result["commit_count"], c_count)
        self.assertEqual(result["open_issues"], i_count)
        self.assertEqual(result["vulnerabilities"], v_count)

if __name__ == "__main__":
    unittest.main()