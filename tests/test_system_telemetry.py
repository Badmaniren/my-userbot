import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import time
from typing import List, Dict, Any

from skills.system_telemetry import SystemTelemetry, SystemTelemetryError

class TestSystemTelemetry(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/{uuid.uuid4().hex}"
        self.telemetry = SystemTelemetry(repo_path=self.repo_path)

    def test_init_creates_valid_state(self):
        self.assertEqual(self.telemetry.repo_path, self.repo_path)
        self.assertIsInstance(self.telemetry.metrics_store, dict)
        self.assertEqual(len(self.telemetry.metrics_store), 0)

    def test_record_and_get_metric(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        value1 = random.uniform(1.0, 50.0)
        value2 = random.uniform(51.0, 100.0)

        self.telemetry.record_metric(metric_name, value1)
        self.telemetry.record_metric(metric_name, value2)

        history = self.telemetry.get_metric_history(metric_name)
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 2)
        self.assertIn(value1, history)
        self.assertIn(value2, history)

    def test_get_nonexistent_metric_history(self):
        fake_metric = uuid.uuid4().hex
        history = self.telemetry.get_metric_history(fake_metric)
        self.assertIsInstance(history, list)
        self.assertEqual(len(history), 0)

    def test_collect_system_snapshot_with_psutil(self):
        mock_psutil = MagicMock()
        mock_psutil.cpu_percent.return_value = random.uniform(5.0, 95.0)
        mock_mem = MagicMock()
        mock_mem.percent = random.uniform(10.0, 90.0)
        mock_mem.available = random.randint(1000000, 8000000000)
        mock_psutil.virtual_memory.return_value = mock_mem

        with patch('skills.system_telemetry.psutil', mock_psutil):
            snapshot = self.telemetry.collect_system_snapshot()

            self.assertIsInstance(snapshot, dict)
            self.assertIn("cpu_percent", snapshot)
            self.assertIn("memory_percent", snapshot)
            self.assertIn("timestamp", snapshot)
            self.assertGreaterEqual(snapshot["cpu_percent"], 0.0)
            self.assertEqual(snapshot["cpu_percent"], mock_psutil.cpu_percent.return_value)
            self.assertEqual(snapshot["memory_percent"], mock_mem.percent)
            self.assertEqual(snapshot["memory_available"], mock_mem.available)

    def test_collect_system_snapshot_without_psutil(self):
        with patch('skills.system_telemetry.psutil', None):
            snapshot = self.telemetry.collect_system_snapshot()

            self.assertIsInstance(snapshot, dict)
            self.assertEqual(snapshot["cpu_percent"], 0.0)
            self.assertEqual(snapshot["memory_percent"], 0.0)
            self.assertEqual(snapshot["memory_available"], 0)
            self.assertIn("timestamp", snapshot)

    def test_collect_system_metrics(self):
        metrics = self.telemetry.collect_system_metrics()
        self.assertIn("cpu_percent", metrics)
        self.assertIn("memory_percent", metrics)
        self.assertIn("cpu_percent", self.telemetry.metrics_store)
        self.assertIn("memory_percent", self.telemetry.metrics_store)

    def test_monitor_engine_health(self):
        health = self.telemetry.monitor_engine_health()
        self.assertIn("status", health)
        self.assertIn(health["status"], ["healthy", "degraded"])
        self.assertIn("metrics", health)

    def test_timers(self):
        timer_name = "test_timer"
        self.telemetry.start_timer(timer_name)
        time.sleep(0.01)
        elapsed = self.telemetry.stop_timer(timer_name)
        self.assertGreater(elapsed, 0.0)
        self.assertIn(f"timer_{timer_name}", self.telemetry.metrics_store)

    def test_stop_nonexistent_timer(self):
        elapsed = self.telemetry.stop_timer("nonexistent")
        self.assertEqual(elapsed, 0.0)

    def test_track_execution_and_log_evolution_cycle(self):
        cycle_id = "cycle_123"
        log = self.telemetry.log_evolution_cycle(cycle_id, {"key": "value"})
        self.assertEqual(log["cycle_id"], cycle_id)
        self.assertIn(f"cycle_{cycle_id}", self.telemetry.execution_logs)

        exec_res = self.telemetry.track_execution("exec_1", {"m1": 10.0})
        self.assertEqual(exec_res["execution_id"], "exec_1")

    def test_analyze_telemetry_trends(self):
        metric_name = uuid.uuid4().hex
        for _ in range(5):
            self.telemetry.record_metric(metric_name, random.uniform(10.0, 50.0))

        analysis = self.telemetry.analyze_telemetry_trends(metric_name)
        self.assertIsInstance(analysis, dict)
        self.assertIn("average", analysis)
        self.assertIn("max", analysis)
        self.assertIn("min", analysis)
        self.assertIn("trend", analysis)

    def test_analyze_telemetry_trends_empty(self):
        fake_metric = uuid.uuid4().hex
        analysis = self.telemetry.analyze_telemetry_trends(fake_metric)
        self.assertIsInstance(analysis, dict)
        self.assertEqual(analysis.get("average"), 0.0)

    def test_export_telemetry_report(self):
        metric_name = uuid.uuid4().hex
        self.telemetry.record_metric(metric_name, random.uniform(100.0, 500.0))

        report_path = f"/tmp/{uuid.uuid4().hex}.json"
        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            result = self.telemetry.export_telemetry_report(report_path)
            self.assertTrue(result)
            mock_file.assert_called_once_with(report_path, 'w', encoding='utf-8')

    def test_export_telemetry_report_error(self):
        report_path = f"/tmp/{uuid.uuid4().hex}.json"
        with patch("builtins.open", side_effect=PermissionError("Access denied")):
            with self.assertRaises(SystemTelemetryError):
                self.telemetry.export_telemetry_report(report_path)

if __name__ == '__main__':
    unittest.main()
