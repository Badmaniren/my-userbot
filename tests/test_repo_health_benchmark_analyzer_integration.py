import unittest
import uuid
import random
import os
from skills.repo_health_benchmark_analyzer import RepoHealthBenchmarkAnalyzer, analyze_repository_benchmark

class TestRepoHealthBenchmarkAnalyzerIntegration(unittest.TestCase):

    def test_repo_health_benchmark_analyzer_integration(self):
        random_run_id = str(uuid.uuid4())
        random_repo_path = f"/tmp/repo_{uuid.uuid4().hex[:6]}"
        random_metric_value = round(random.uniform(50.0, 150.0), 2)
        random_threshold = 100.0

        analyzer = RepoHealthBenchmarkAnalyzer()
        metric_key = f"metric_{random_run_id[:8]}"

        analysis_result = analyzer.analyze_benchmarks(
            metric_key=metric_key,
            metric_value=random_metric_value,
            benchmark_limit=random_threshold
        )

        self.assertEqual(analysis_result["metric_key"], metric_key)
        self.assertEqual(analysis_result["metric_value"], random_metric_value)
        self.assertEqual(analysis_result["benchmark_limit"], random_threshold)
        
        expected_is_anomaly = random_metric_value > random_threshold
        self.assertEqual(analysis_result["is_anomaly"], expected_is_anomaly)
        self.assertEqual(analysis_result["status"], "WARNING" if expected_is_anomaly else "OK")

        self.assertIn(analysis_result, analyzer.metrics)

        report = analyze_repository_benchmark(
            repo_path=random_repo_path,
            run_id=random_run_id,
            metric_value=random_metric_value,
            anomaly_threshold=random_threshold
        )

        self.assertEqual(report["repo_path"], random_repo_path)
        self.assertEqual(report["run_id"], random_run_id)
        self.assertIsInstance(report["analysis"], dict)
        self.assertEqual(report["analysis"]["metric_value"], random_metric_value)
        self.assertEqual(report["analysis"]["benchmark_limit"], random_threshold)

if __name__ == "__main__":
    unittest.main()