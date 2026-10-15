import unittest
import os
import tempfile
import uuid
import random
import time
from skills.system_telemetry import SystemTelemetry, SystemTelemetryError

class TestSystemTelemetryIntegration(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.repo_path = self.temp_dir.name
        self.telemetry = SystemTelemetry(repo_path=self.repo_path)

        self.cycle_id = str(uuid.uuid4())
        self.random_metric_key = f"metric_{uuid.uuid4().hex[:8]}"
        self.random_metric_value = random.randint(100, 1000)
        self.operation_name = f"op_{uuid.uuid4().hex[:6]}"

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_full_telemetry_pipeline_integration(self):
        self.telemetry.start_timer(self.operation_name)

        with self.telemetry.track_execution(self.operation_name):
            time.sleep(0.05)
            sys_metrics = self.telemetry.collect_system_metrics()
            self.assertIn("cpu_usage", sys_metrics)
            self.assertIn("memory_usage", sys_metrics)

            self.telemetry.log_metric(self.random_metric_key, self.random_metric_value)

        duration = self.telemetry.stop_timer(self.operation_name)
        self.assertGreater(duration, 0.0)

        evolution_metrics = {
            "duration": duration,
            "random_score": random.random(),
            self.random_metric_key: self.random_metric_value
        }

        self.telemetry.log_evolution_cycle(self.cycle_id, evolution_metrics)

        health_data = self.telemetry.monitor_engine_health()
        self.assertEqual(health_data["repo_status"], "active")
        self.assertIn("cpu_usage", health_data)
        self.assertIn("memory_usage", health_data)
        self.assertIn("uptime", health_data)
        self.assertIn("active_threads", health_data)

        report_filename = os.path.join(self.repo_path, f"report_{uuid.uuid4().hex}.json")
        dumped_path = self.telemetry.dump_telemetry_report(report_filename)

        self.assertTrue(os.path.exists(dumped_path))

        with open(dumped_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn(self.random_metric_key, content)
            self.assertIn(str(self.random_metric_value), content)

    def test_system_telemetry_invalid_repo_path(self):
        invalid_path = os.path.join(self.repo_path, str(uuid.uuid4()))
        telemetry_invalid = SystemTelemetry(repo_path=invalid_path)
        health = telemetry_invalid.monitor_engine_health()
        self.assertEqual(health["repo_status"], "unknown")

if __name__ == "__main__":
    unittest.main()