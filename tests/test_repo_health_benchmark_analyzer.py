import unittest
import uuid
import random
import logging
from unittest.mock import patch, MagicMock
from skills.repo_health_benchmark_analyzer import RepoHealthBenchmarkAnalyzer, analyze_repository_benchmark

logging.disable(logging.CRITICAL)

class TestRepoHealthBenchmarkAnalyzer(unittest.TestCase):

    def setUp(self):
        self.analyzer = RepoHealthBenchmarkAnalyzer()
        self.metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        self.limit = round(random.uniform(10.0, 100.0), 2)

    def test_analyze_benchmarks_normal(self):
        val = round(self.limit - random.uniform(1.0, 5.0), 2)
        res = self.analyzer.analyze_benchmarks(self.metric_key, val, self.limit)
        
        self.assertEqual(res["metric_key"], self.metric_key)
        self.assertEqual(res["metric_value"], val)
        self.assertEqual(res["benchmark_limit"], self.limit)
        self.assertFalse(res["is_anomaly"])
        self.assertEqual(res["status"], "OK")
        self.assertIn(res, self.analyzer.metrics)

    def test_analyze_benchmarks_anomaly(self):
        val = round(self.limit + random.uniform(1.0, 5.0), 2)
        res = self.analyzer.analyze_benchmarks(self.metric_key, val, self.limit)
        
        self.assertEqual(res["metric_key"], self.metric_key)
        self.assertEqual(res["metric_value"], val)
        self.assertEqual(res["benchmark_limit"], self.limit)
        self.assertTrue(res["is_anomaly"])
        self.assertEqual(res["status"], "WARNING")
        self.assertIn(res, self.analyzer.metrics)

    def test_analyze_repository_benchmark_integration(self):
        repo_path = f"/var/repo/{uuid.uuid4().hex[:6]}"
        run_id = uuid.uuid4().hex
        val = round(random.uniform(50.0, 150.0), 2)
        threshold = round(random.uniform(40.0, 100.0), 2)

        report = analyze_repository_benchmark(
            repo_path=repo_path,
            run_id=run_id,
            metric_value=val,
            anomaly_threshold=threshold
        )

        self.assertEqual(report["repo_path"], repo_path)
        self.assertEqual(report["run_id"], run_id)
        
        analysis = report["analysis"]
        expected_key = f"metric_{run_id[:8]}"
        self.assertEqual(analysis["metric_key"], expected_key)
        self.assertEqual(analysis["metric_value"], val)
        self.assertEqual(analysis["benchmark_limit"], threshold)
        self.assertEqual(analysis["is_anomaly"], val > threshold)
        self.assertEqual(analysis["status"], "WARNING" if val > threshold else "OK")

    def test_multiple_metrics_accumulation(self):
        count = random.randint(3, 7)
        for _ in range(count):
            key = f"metric_{uuid.uuid4().hex[:8]}"
            val = round(random.uniform(0.0, 200.0), 2)
            lim = round(random.uniform(50.0, 150.0), 2)
            self.analyzer.analyze_benchmarks(key, val, lim)

        self.assertEqual(len(self.analyzer.metrics), count)

    def test_analyzer_with_mocked_internal_logic(self):
        custom_key = f"dyn_metric_{uuid.uuid4().hex[:5]}"
        custom_val = round(random.uniform(300.0, 500.0), 2)
        custom_limit = round(random.uniform(100.0, 200.0), 2)

        with patch("skills.repo_health_benchmark_analyzer.RepoHealthBenchmarkAnalyzer.analyze_benchmarks") as mock_analyze:
            expected_dict = {
                "metric_key": custom_key,
                "metric_value": custom_val,
                "benchmark_limit": custom_limit,
                "is_anomaly": True,
                "status": "WARNING"
            }
            mock_analyze.return_value = expected_dict

            repo_path = f"/opt/git/{uuid.uuid4().hex[:8]}"
            run_id = uuid.uuid4().hex
            report = analyze_repository_benchmark(repo_path, run_id, custom_val, custom_limit)

            mock_analyze.assert_called_once_with(
                metric_key=f"metric_{run_id[:8]}",
                metric_value=custom_val,
                benchmark_limit=custom_limit
            )
            self.assertEqual(report["analysis"], expected_dict)

if __name__ == "__main__":
    unittest.main()