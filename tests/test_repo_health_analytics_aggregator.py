import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.repo_health_analytics_aggregator import RepoHealthAnalyticsAggregator

class TestRepoHealthAnalyticsAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = RepoHealthAnalyticsAggregator()

    def test_aggregate_metrics_success(self):
        repo_id = str(uuid.uuid4())
        branch_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        commit_count = random.randint(10, 500)
        open_issues = random.randint(0, 50)
        vulnerability_count = random.randint(0, 10)

        raw_metrics = {
            "repo_id": repo_id,
            "branch": branch_name,
            "commits": commit_count,
            "issues": open_issues,
            "vulnerabilities": vulnerability_count,
            "status": "healthy"
        }

        mock_collector = MagicMock()
        mock_collector.fetch_raw_metrics.return_value = raw_metrics

        with patch('skills.repo_health_analytics_aggregator.repo_health_collector', mock_collector):
            result = self.aggregator.aggregate(repo_id)

        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_id"], repo_id)
        self.assertEqual(result["metrics"]["commits"], commit_count)
        self.assertEqual(result["metrics"]["issues"], open_issues)
        self.assertEqual(result["metrics"]["vulnerabilities"], vulnerability_count)
        self.assertIn("aggregated_at", result)

    def test_aggregate_metrics_with_stream_data(self):
        repo_id = str(uuid.uuid4())
        random_hash = uuid.uuid4().hex
        payload = json.dumps({"repo_id": repo_id, "hash": random_hash, "score": random.uniform(50.0, 100.0)}).encode('utf-8')
        
        mock_stream = io.BytesIO(payload)

        with patch('skills.repo_health_analytics_aggregator.open', return_value=mock_stream, create=True):
            result = self.aggregator.aggregate_from_stream(str(uuid.uuid4()))

        self.assertIsInstance(result, dict)
        self.assertEqual(result["repo_id"], repo_id)
        self.assertEqual(result["hash"], random_hash)

    def test_aggregate_metrics_failure_handling(self):
        repo_id = str(uuid.uuid4())
        error_message = ''.join(random.choices(string.ascii_letters, k=15))

        mock_collector = MagicMock()
        mock_collector.fetch_raw_metrics.side_effect = Exception(error_message)

        with patch('skills.repo_health_analytics_aggregator.repo_health_collector', mock_collector):
            with self.assertRaises(Exception) as context:
                self.aggregator.aggregate(repo_id)

            self.assertIn(error_message, str(context.exception))

    def test_calculate_health_score(self):
        commits = random.randint(50, 200)
        issues = random.randint(0, 10)
        vulnerabilities = 0

        metrics = {
            "commits": commits,
            "issues": issues,
            "vulnerabilities": vulnerabilities
        }

        score = self.aggregator._calculate_health_score(metrics)
        self.assertIsInstance(score, float)
        self.assertTrue(0.0 <= score <= 100.0)

    def test_aggregate_batch_reports(self):
        batch_size = random.randint(3, 10)
        repo_ids = [str(uuid.uuid4()) for _ in range(batch_size)]
        
        mock_collector = MagicMock()
        mock_collector.fetch_raw_metrics.side_effect = lambda rid: {
            "repo_id": rid,
            "commits": random.randint(1, 100),
            "issues": random.randint(0, 5),
            "vulnerabilities": 0
        }

        with patch('skills.repo_health_analytics_aggregator.repo_health_collector', mock_collector):
            batch_result = self.aggregator.aggregate_batch(repo_ids)

        self.assertIsInstance(batch_result, list)
        self.assertEqual(len(batch_result), batch_size)
        for idx, res in enumerate(batch_result):
            self.assertEqual(res["repo_id"], repo_ids[idx])
            self.assertIn("metrics", res)

if __name__ == '__main__':
    unittest.main()