import json
import os
import random
import tempfile
import unittest
import uuid

from skills.repo_health_trend_calculator import (
    RepoHealthTrendCalculator,
    calculate_health_trends,
)


class TestRepoHealthTrendCalculatorIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp_dir.cleanup)
        self.repo_id = f"repo-{uuid.uuid4()}"
        self.metric_keys = ["coverage", "vulnerabilities", "code_smells", "build_success_rate"]

    def _generate_metric_history(self, num_points=5):
        history = []
        base_coverage = random.uniform(50.0, 80.0)
        base_vulns = random.randint(10, 30)

        for i in range(num_points):
            snapshot = {
                "snapshot_id": str(uuid.uuid4()),
                "timestamp": 1700000000 + i * 86400,
                "metrics": {
                    "coverage": round(base_coverage + i * random.uniform(0.5, 2.0), 2),
                    "vulnerabilities": max(0, base_vulns - i * random.randint(1, 3)),
                    "code_smells": random.randint(5, 50),
                    "build_success_rate": round(random.uniform(0.85, 1.0), 4),
                },
            }
            history.append(snapshot)
        return history

    def test_trend_calculator_class_with_real_history(self):
        history_data = self._generate_metric_history(num_points=6)
        calculator = RepoHealthTrendCalculator()

        result = calculator.calculate_trends(repo_id=self.repo_id, history=history_data)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, dict)
        self.assertEqual(result.get("repo_id"), self.repo_id)
        self.assertIn("trends", result)

        trends = result["trends"]
        for key in self.metric_keys:
            self.assertIn(key, trends)
            metric_trend = trends[key]
            self.assertIn("direction", metric_trend)
            self.assertIn("delta", metric_trend)
            self.assertIn("historical_values", metric_trend)
            self.assertEqual(len(metric_trend["historical_values"]), 6)

        # Verify exact dynamic delta calculation for coverage
        initial_coverage = history_data[0]["metrics"]["coverage"]
        final_coverage = history_data[-1]["metrics"]["coverage"]
        expected_coverage_delta = round(final_coverage - initial_coverage, 2)
        actual_coverage_delta = round(trends["coverage"]["delta"], 2)

        self.assertEqual(actual_coverage_delta, expected_coverage_delta)
        self.assertEqual(trends["coverage"]["direction"], "upward" if expected_coverage_delta > 0 else "downward")

    def test_trend_calculator_file_persistence_integration(self):
        history_data = self._generate_metric_history(num_points=4)
        input_file_path = os.path.join(self.temp_dir.name, f"history_{uuid.uuid4().hex}.json")
        output_file_path = os.path.join(self.temp_dir.name, f"trends_{uuid.uuid4().hex}.json")

        payload = {
            "repo_id": self.repo_id,
            "history": history_data,
        }

        with open(input_file_path, "w", encoding="utf-8") as f:
            json.dump(payload, f)

        # Call function directly without mocking
        result = calculate_health_trends(
            input_file=input_file_path,
            output_file=output_file_path,
        )

        self.assertTrue(os.path.exists(output_file_path), "Output trends file was not created on disk")

        with open(output_file_path, "r", encoding="utf-8") as f:
            saved_data = json.load(f)

        self.assertEqual(saved_data["repo_id"], self.repo_id)
        self.assertIn("trends", saved_data)
        self.assertIn("summary", saved_data)

        vuln_delta = saved_data["trends"]["vulnerabilities"]["delta"]
        initial_vulns = history_data[0]["metrics"]["vulnerabilities"]
        final_vulns = history_data[-1]["metrics"]["vulnerabilities"]
        self.assertEqual(vuln_delta, final_vulns - initial_vulns)

    def test_trend_calculator_handles_empty_or_single_history(self):
        single_snapshot = self._generate_metric_history(num_points=1)
        calculator = RepoHealthTrendCalculator()

        result = calculator.calculate_trends(repo_id=self.repo_id, history=single_snapshot)

        self.assertEqual(result.get("repo_id"), self.repo_id)
        for key in self.metric_keys:
            self.assertEqual(result["trends"][key]["delta"], 0)
            self.assertEqual(result["trends"][key]["direction"], "stable")


if __name__ == "__main__":
    unittest.main()