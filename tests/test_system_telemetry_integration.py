import unittest
import os
import tempfile
import uuid
import random
from skills.system_telemetry import SystemTelemetry, SystemTelemetryError
from skills.git_inspector import GitInspector


class TestSystemTelemetryIntegration(unittest.TestCase):

    def setUp(self):
        self.test_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.test_dir.name

        self.git_inspector = GitInspector(repo_path=self.repo_path)

        self.telemetry = SystemTelemetry(
            repo_path=self.repo_path,
            git_inspector=self.git_inspector
        )

        self.random_metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_metric_value = round(random.uniform(10.0, 99.9), 2)

    def tearDown(self):
        self.test_dir.cleanup()

    def test_collect_and_monitor_performance_metrics(self):
        metrics = self.telemetry.collect_performance_metrics()
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_percent", metrics)
        self.assertIn("disk_percent", metrics)

        monitored = self.telemetry.monitor_resources()
        self.assertEqual(metrics.keys(), monitored.keys())

    def test_log_telemetry_and_read_stream(self):
        stream_id = str(uuid.uuid4())

        logged = self.telemetry.log_telemetry(self.random_metric_name, self.random_metric_value)
        self.assertTrue(logged)

        stream_data = self.telemetry.read_telemetry_stream(stream_id)
        self.assertGreater(len(stream_data), 0)

        found = False
        for line in stream_data:
            if self.random_metric_name in line:
                found = True
                break
        self.assertTrue(found, "Записанная метрика не найдена в потоке телеметрии")

    def test_analyze_patch_success_rate_with_real_history(self):
        analysis = self.telemetry.analyze_patch_success_rate()

        self.assertIn("total_patches", analysis)
        self.assertIn("successful_patches", analysis)
        self.assertIn("failed_patches", analysis)
        self.assertIn("success_rate", analysis)

        self.assertIsInstance(analysis["total_patches"], int)
        self.assertIsInstance(analysis["success_rate"], float)


if __name__ == "__main__":
    unittest.main()