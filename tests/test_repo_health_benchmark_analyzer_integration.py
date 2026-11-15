import unittest
import uuid
import random
from skills.repo_health_benchmark_analyzer import RepoHealthBenchmarkAnalyzer, analyze_repository_benchmark

class TestRepoHealthBenchmarkAnalyzerIntegration(unittest.TestCase):
    def test_end_to_end_benchmark_analysis_and_degradation(self):
        random_repo_name = f"repo_test_{uuid.uuid4().hex[:8]}"
        random_run_id = str(uuid.uuid4())
        
        baseline_limit = round(random.uniform(50.0, 100.0), 2)
        normal_metric_value = round(baseline_limit - random.uniform(1.0, 10.0), 2)
        degraded_metric_value = round(baseline_limit + random.uniform(1.0, 20.0), 2)
        
        analyzer = RepoHealthBenchmarkAnalyzer()
        
        normal_key = f"metric_norm_{uuid.uuid4().hex[:6]}"
        normal_result = analyzer.analyze_benchmarks(
            metric_key=normal_key,
            metric_value=normal_metric_value,
            benchmark_limit=baseline_limit
        )
        
        self.assertEqual(normal_result["metric_key"], normal_key)
        self.assertEqual(normal_result["metric_value"], normal_metric_value)
        self.assertEqual(normal_result["benchmark_limit"], baseline_limit)
        self.assertFalse(normal_result["is_anomaly"])
        self.assertEqual(normal_result["status"], "OK")
        
        degraded_key = f"metric_deg_{uuid.uuid4().hex[:6]}"
        degraded_result = analyzer.analyze_benchmarks(
            metric_key=degraded_key,
            metric_value=degraded_metric_value,
            benchmark_limit=baseline_limit
        )
        
        self.assertEqual(degraded_result["metric_key"], degraded_key)
        self.assertEqual(degraded_result["metric_value"], degraded_metric_value)
        self.assertEqual(degraded_result["benchmark_limit"], baseline_limit)
        self.assertTrue(degraded_result["is_anomaly"])
        self.assertEqual(degraded_result["status"], "WARNING")
        
        self.assertEqual(len(analyzer.metrics), 2)
        self.assertIn(normal_result, analyzer.metrics)
        self.assertIn(degraded_result, analyzer.metrics)
        
        report = analyze_repository_benchmark(
            repo_path=random_repo_name,
            run_id=random_run_id,
            metric_value=degraded_metric_value,
            anomaly_threshold=baseline_limit
        )
        
        self.assertIsInstance(report, dict)
        self.assertEqual(report["repo_path"], random_repo_name)
        self.assertEqual(report["run_id"], random_run_id)
        self.assertIn("analysis", report)
        
        sub_analysis = report["analysis"]
        self.assertEqual(sub_analysis["metric_key"], f"metric_{random_run_id[:8]}")
        self.assertEqual(sub_analysis["metric_value"], degraded_metric_value)
        self.assertEqual(sub_analysis["benchmark_limit"], baseline_limit)
        self.assertTrue(sub_analysis["is_anomaly"])
        self.assertEqual(sub_analysis["status"], "WARNING")

if __name__ == "__main__":
    unittest.main()