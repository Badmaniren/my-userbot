import unittest
import uuid
import random
import string
from unittest.mock import patch

from skills.repo_health_benchmark_analyzer import (
    RepoHealthBenchmarkAnalyzer,
    analyze_repository_benchmark
)

class TestRepoHealthBenchmarkAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RepoHealthBenchmarkAnalyzer()
        self.metric_key = f"metric_{uuid.uuid4().hex[:8]}"

    def test_analyze_benchmarks_ok(self):
        limit = random.uniform(50.0, 100.0)
        value = limit - random.uniform(1.0, 20.0)
        
        result = self.analyzer.analyze_benchmarks(self.metric_key, value, limit)
        
        self.assertEqual(result["metric_key"], self.metric_key)
        self.assertEqual(result["metric_value"], value)
        self.assertEqual(result["benchmark_limit"], limit)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["status"], "OK")
        self.assertIn(result, self.analyzer.metrics)

    def test_analyze_benchmarks_anomaly(self):
        limit = random.uniform(10.0, 50.0)
        value = limit + random.uniform(1.0, 50.0)
        
        result = self.analyzer.analyze_benchmarks(self.metric_key, value, limit)
        
        self.assertEqual(result["metric_key"], self.metric_key)
        self.assertEqual(result["metric_value"], value)
        self.assertEqual(result["benchmark_limit"], limit)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["status"], "WARNING")
        self.assertIn(result, self.analyzer.metrics)

    def test_analyze_repository_benchmark_integration(self):
        repo_path = f"/var/repo/{uuid.uuid4().hex}"
        run_id = uuid.uuid4().hex
        metric_value = random.uniform(100.0, 500.0)
        threshold = random.uniform(200.0, 400.0)

        report = analyze_repository_benchmark(
            repo_path=repo_path,
            run_id=run_id,
            metric_value=metric_value,
            anomaly_threshold=threshold
        )

        self.assertEqual(report["repo_path"], repo_path)
        self.assertEqual(report["run_id"], run_id)
        
        analysis = report["analysis"]
        expected_metric_key = f"metric_{run_id[:8]}"
        self.assertEqual(analysis["metric_key"], expected_metric_key)
        self.assertEqual(analysis["metric_value"], metric_value)
        self.assertEqual(analysis["benchmark_limit"], threshold)
        self.assertEqual(analysis["is_anomaly"], metric_value > threshold)
        self.assertEqual(analysis["status"], "WARNING" if metric_value > threshold else "OK")

    def test_multiple_metrics_accumulation(self):
        iterations = random.randint(3, 10)
        for _ in range(iterations):
            key = f"metric_{uuid.uuid4().hex[:6]}"
            val = random.uniform(0.0, 100.0)
            lim = random.uniform(50.0, 80.0)
            self.analyzer.analyze_benchmarks(key, val, lim)

        self.assertEqual(len(self.analyzer.metrics), iterations)

    def test_analyze_repository_benchmark_mocked_class(self):
        repo_path = f"/home/user/project_{uuid.uuid4().hex[:6]}"
        run_id = uuid.uuid4().hex
        metric_value = random.uniform(10.0, 90.0)
        threshold = random.uniform(15.0, 85.0)

        mock_return_value = {
            "metric_key": f"metric_{run_id[:8]}",
            "metric_value": metric_value,
            "benchmark_limit": threshold,
            "is_anomaly": True,
            "status": "WARNING"
        }

        with patch('skills.repo_health_benchmark_analyzer.RepoHealthBenchmarkAnalyzer') as MockAnalyzer:
            instance = MockAnalyzer.return_value
            instance.analyze_benchmarks.return_value = mock_return_value

            report = analyze_repository_benchmark(
                repo_path=repo_path,
                run_id=run_id,
                metric_value=metric_value,
                anomaly_threshold=threshold
            )

            MockAnalyzer.assert_called_once()
            instance.analyze_benchmarks.assert_called_once_with(
                metric_key=f"metric_{run_id[:8]}",
                metric_value=metric_value,
                benchmark_limit=threshold
            )

            self.assertEqual(report["repo_path"], repo_path)
            self.assertEqual(report["run_id"], run_id)
            self.assertEqual(report["analysis"], mock_return_value)

if __name__ == '__main__':
    unittest.main()