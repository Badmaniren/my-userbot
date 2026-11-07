import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.repo_performance_analyzer import RepoPerformanceAnalyzer

class TestRepoPerformanceAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RepoPerformanceAnalyzer()
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_metric_value = random.uniform(10.0, 500.0)
        self.random_threshold = random.uniform(50.0, 300.0)
        self.random_log_id = uuid.uuid4().hex

    def test_analyze_metrics_valid_data(self):
        raw_data = f"METRIC:{self.random_metric_name}:{self.random_metric_value}:{self.random_log_id}".encode('utf-8')
        mock_stream = io.BytesIO(raw_data)

        with patch('skills.repo_performance_analyzer.open', return_value=mock_stream, create=True):
            result = self.analyzer.analyze_metric_stream(self.random_log_id, self.random_threshold)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('log_id'), self.random_log_id)
        self.assertEqual(result.get('metric_name'), self.random_metric_name)
        self.assertEqual(result.get('value'), self.random_metric_value)
        
        expected_bottleneck = self.random_metric_value > self.random_threshold
        self.assertEqual(result.get('is_bottleneck'), expected_bottleneck)

    def test_analyze_metrics_empty_stream(self):
        mock_stream = io.BytesIO(b"")

        with patch('skills.repo_performance_analyzer.open', return_value=mock_stream, create=True):
            result = self.analyzer.analyze_metric_stream(self.random_log_id, self.random_threshold)

        self.assertIsInstance(result, dict)
        self.assertEqual(result.get('log_id'), self.random_log_id)
        self.assertFalse(result.get('is_bottleneck'))
        self.assertIsNone(result.get('metric_name'))

    def test_aggregate_repository_performance(self):
        metric_count = random.randint(3, 8)
        lines = []
        target_metrics = []

        for _ in range(metric_count):
            m_name = ''.join(random.choices(string.ascii_lowercase, k=6))
            m_val = random.uniform(1.0, 1000.0)
            lines.append(f"{m_name}:{m_val}\n")
            target_metrics.append((m_name, m_val))

        raw_data = "".join(lines).encode('utf-8')
        mock_stream = io.BytesIO(raw_data)

        with patch('skills.repo_performance_analyzer.open', return_value=mock_stream, create=True):
            summary = self.analyzer.aggregate_performance(uuid.uuid4().hex)

        self.assertIsInstance(summary, dict)
        self.assertIn('total_metrics_analyzed', summary)
        self.assertEqual(summary['total_metrics_analyzed'], metric_count)
        self.assertIn('max_value', summary)

    def test_detect_performance_regression(self):
        baseline_val = random.uniform(10.0, 50.0)
        current_val = baseline_val + random.uniform(60.0, 200.0)
        
        regression_data = {
            'baseline': baseline_val,
            'current': current_val,
            'metric_id': self.random_log_id
        }

        with patch.object(self.analyzer, '_fetch_historical_data', return_value=baseline_val):
            is_regressed, diff = self.analyzer.detect_regression(self.random_log_id, current_val)

        self.assertTrue(is_regressed)
        self.assertAlmostEqual(diff, current_val - baseline_val)

if __name__ == '__main__':
    unittest.main()