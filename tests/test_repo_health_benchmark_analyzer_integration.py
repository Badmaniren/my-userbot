import unittest
import uuid
import random
import os
from skills.repo_health_benchmark_analyzer import RepoHealthBenchmarkAnalyzer, analyze_repository_benchmark

class TestRepoHealthBenchmarkAnalyzerIntegration(unittest.TestCase):
    def test_repository_benchmark_end_to_end_integration(self):
        random_repo_name = f"repo_{uuid.uuid4().hex[:8]}"
        random_run_id = str(uuid.uuid4())
        
        random_limit = round(random.uniform(50.0, 150.0), 2)
        # Генерируем значение, которое гарантированно вызовет аномалию или будет в норме
        is_anomaly_case = random.choice([True, False])
        if is_anomaly_case:
            random_metric_val = random_limit + round(random.uniform(1.0, 50.0), 2)
            expected_status = "WARNING"
        else:
            random_metric_val = max(0.0, random_limit - round(random.uniform(1.0, 50.0), 2))
            expected_status = "OK"

        report = analyze_repository_benchmark(
            repo_path=random_repo_name,
            run_id=random_run_id,
            metric_value=random_metric_val,
            anomaly_threshold=random_limit
        )

        self.assertIsInstance(report, dict)
        self.assertEqual(report.get("repo_path"), random_repo_name)
        self.assertEqual(report.get("run_id"), random_run_id)

        analysis = report.get("analysis")
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get("metric_value"), random_metric_val)
        self.assertEqual(analysis.get("benchmark_limit"), random_limit)
        self.assertEqual(analysis.get("is_anomaly"), is_anomaly_case)
        self.assertEqual(analysis.get("status"), expected_status)
        self.assertTrue(analysis.get("metric_key").startswith("metric_"))

        analyzer = RepoHealthBenchmarkAnalyzer()
        second_metric_key = f"metric_{uuid.uuid4().hex[:6]}"
        second_limit = round(random.uniform(10.0, 100.0), 2)
        second_value = round(random.uniform(0.0, 200.0), 2)
        
        result_direct = analyzer.analyze_benchmarks(
            metric_key=second_metric_key,
            metric_value=second_value,
            benchmark_limit=second_limit
        )

        self.assertIsInstance(result_direct, dict)
        self.assertEqual(len(analyzer.metrics), 1)
        self.assertEqual(analyzer.metrics[0], result_direct)
        self.assertEqual(result_direct.get("metric_key"), second_metric_key)

if __name__ == "__main__":
    unittest.main()