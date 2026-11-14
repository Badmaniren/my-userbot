import unittest
import uuid
import random
from unittest.mock import patch

from skills.repo_health_benchmark_analyzer import (
    RepoHealthBenchmarkAnalyzer,
    analyze_repository_benchmark
)

class TestRepoHealthBenchmarkAnalyzer(unittest.TestCase):
    def setUp(self):
        self.analyzer = RepoHealthBenchmarkAnalyzer()

    def test_analyze_benchmarks_ok(self):
        metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(10.0, 50.0)
        benchmark_limit = metric_value + random.uniform(1.0, 20.0)

        result = self.analyzer.analyze_benchmarks(metric_key, metric_value, benchmark_limit)

        self.assertEqual(result["metric_key"], metric_key)
        self.assertEqual(result["metric_value"], metric_value)
        self.assertEqual(result["benchmark_limit"], benchmark_limit)
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["status"], "OK")
        self.assertIn(result, self.analyzer.metrics)

    def test_analyze_benchmarks_anomaly(self):
        metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        benchmark_limit = random.uniform(10.0, 50.0)
        metric_value = benchmark_limit + random.uniform(1.0, 20.0)

        result = self.analyzer.analyze_benchmarks(metric_key, metric_value, benchmark_limit)

        self.assertEqual(result["metric_key"], metric_key)
        self.assertEqual(result["metric_value"], metric_value)
        self.assertEqual(result["benchmark_limit"], benchmark_limit)
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["status"], "WARNING")
        self.assertIn(result, self.analyzer.metrics)

    def test_analyze_repository_benchmark_integration(self):
        repo_path = f"/repo/{uuid.uuid4().hex[:6]}"
        run_id = uuid.uuid4().hex
        benchmark_limit = random.uniform(50.0, 100.0)
        metric_value = benchmark_limit + random.uniform(0.1, 50.0)

        report = analyze_repository_benchmark(
            repo_path=repo_path,
            run_id=run_id,
            metric_value=metric_value,
            anomaly_threshold=benchmark_limit
        )

        self.assertEqual(report["repo_path"], repo_path)
        self.assertEqual(report["run_id"], run_id)
        
        analysis = report["analysis"]
        self.assertEqual(analysis["metric_key"], f"metric_{run_id[:8]}")
        self.assertEqual(analysis["metric_value"], metric_value)
        self.assertEqual(analysis["benchmark_limit"], benchmark_limit)
        self.assertTrue(analysis["is_anomaly"])
        self.assertEqual(analysis["status"], "WARNING")

    def test_analyze_repository_benchmark_no_anomaly(self):
        repo_path = f"/var/git/{uuid.uuid4().hex[:6]}"
        run_id = uuid.uuid4().hex
        metric_value = random.uniform(10.0, 40.0)
        benchmark_limit = metric_value + random.uniform(10.0, 50.0)

        report = analyze_repository_benchmark(
            repo_path=repo_path,
            run_id=run_id,
            metric_value=metric_value,
            anomaly_threshold=benchmark_limit
        )

        self.assertEqual(report["repo_path"], repo_path)
        self.assertEqual(report["run_id"], run_id)
        
        analysis = report["analysis"]
        self.assertEqual(analysis["metric_key"], f"metric_{run_id[:8]}")
        self.assertEqual(analysis["metric_value"], metric_value)
        self.assertEqual(analysis["benchmark_limit"], benchmark_limit)
        self.assertFalse(analysis["is_anomaly"])
        self.assertEqual(analysis["status"], "OK")

if __name__ == "__main__":
    unittest.main()