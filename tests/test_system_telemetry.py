import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import time
import os
import io
from skills.system_telemetry import SystemTelemetry, SystemTelemetryError

class TestSystemTelemetry(unittest.TestCase):

    def setUp(self):
        self.repo_path_val = uuid.uuid4().hex
        self.telemetry = SystemTelemetry(repo_path=self.repo_path_val)

    def test_init_defaults(self):
        telemetry_default = SystemTelemetry()
        self.assertIsNone(telemetry_default.repo_path)
        self.assertIsInstance(telemetry_default.start_time, float)
        self.assertEqual(telemetry_default.metrics_cache, {})
        self.assertEqual(telemetry_default._timers, {})

    def test_log_evolution_cycle(self):
        cycle_id = uuid.uuid4().hex
        metric_key = uuid.uuid4().hex
        metric_val = random.randint(1, 1000)
        metrics = {metric_key: metric_val}

        with patch("skills.system_telemetry.logger.info") as mock_logger_info:
            self.telemetry.log_evolution_cycle(cycle_id, metrics)
            mock_logger_info.assert_called_once()
            args, _ = mock_logger_info.call_args
            self.assertIn(cycle_id, args[0])
            self.assertIn(str(metric_val), args[0])

    def test_collect_system_metrics_success(self):
        mock_psutil = unittest.mock.MagicMock()
        cpu_val = random.uniform(0.0, 100.0)
        mem_val = random.uniform(0.0, 100.0)
        mock_psutil.cpu_percent.return_value = cpu_val
        mock_psutil.virtual_memory.return_value.percent = mem_val

        with patch("skills.system_telemetry.psutil", mock_psutil):
            metrics = self.telemetry.collect_system_metrics()
            self.assertEqual(metrics["cpu_usage"], cpu_val)
            self.assertEqual(metrics["memory_usage"], mem_val)

    def test_collect_system_metrics_exception(self):
        mock_psutil = unittest.mock.MagicMock()
        mock_psutil.cpu_percent.side_effect = Exception(uuid.uuid4().hex)
        with patch("skills.system_telemetry.psutil", mock_psutil):
            with self.assertRaises(SystemTelemetryError):
                self.telemetry.collect_system_metrics()

    @patch("skills.system_telemetry.os.path.exists")
    @patch("skills.system_telemetry.threading.active_count")
    def test_monitor_engine_health(self, mock_active_count, mock_exists):
        mock_psutil = unittest.mock.MagicMock()
        cpu_val = random.uniform(0.0, 100.0)
        mem_val = random.uniform(0.0, 100.0)
        threads_val = random.randint(1, 50)

        mock_psutil.cpu_percent.return_value = cpu_val
        mock_psutil.virtual_memory.return_value.percent = mem_val
        mock_active_count.return_value = threads_val
        mock_exists.return_value = True

        with patch("skills.system_telemetry.psutil", mock_psutil):
            health = self.telemetry.monitor_engine_health()
            self.assertEqual(health["cpu_usage"], cpu_val)
            self.assertEqual(health["memory_usage"], mem_val)
            self.assertEqual(health["active_threads"], threads_val)
            self.assertEqual(health["repo_status"], "active")
            self.assertIn("uptime", health)

    @patch("skills.system_telemetry.os.path.exists")
    def test_monitor_engine_health_unknown_repo(self, mock_exists):
        mock_psutil = unittest.mock.MagicMock()
        mock_psutil.cpu_percent.return_value = 10.0
        mock_exists.return_value = False
        telemetry_no_repo = SystemTelemetry(repo_path=uuid.uuid4().hex)
        with patch("skills.system_telemetry.psutil", mock_psutil):
            health = telemetry_no_repo.monitor_engine_health()
            self.assertEqual(health["repo_status"], "unknown")

    def test_monitor_engine_health_exception(self):
        mock_psutil = unittest.mock.MagicMock()
        mock_psutil.cpu_percent.side_effect = Exception(uuid.uuid4().hex)
        with patch("skills.system_telemetry.psutil", mock_psutil):
            with self.assertRaises(SystemTelemetryError):
                self.telemetry.monitor_engine_health()

    def test_dump_telemetry_report(self):
        filename = f"{uuid.uuid4().hex}.json"
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        self.telemetry.log_metric(key, val)

        mock_file = mock_open()
        with patch("builtins.open", mock_file):
            res_filename = self.telemetry.dump_telemetry_report(filename)
            self.assertEqual(res_filename, filename)
            mock_file.assert_called_once_with(filename, "w", encoding="utf-8")

    def test_track_execution(self):
        op_name = uuid.uuid4().hex
        with patch("skills.system_telemetry.logger.debug") as mock_debug:
            with self.telemetry.track_execution(op_name):
                pass
            mock_debug.assert_called_once()
            args, _ = mock_debug.call_args
            self.assertIn(op_name, args[0])

    def test_log_and_get_metric(self):
        key = uuid.uuid4().hex
        val = uuid.uuid4().hex
        self.telemetry.log_metric(key, val)
        metrics = self.telemetry.get_metrics()
        self.assertEqual(metrics[key], val)

    def test_timers(self):
        timer_name = uuid.uuid4().hex
        self.telemetry.start_timer(timer_name)
        time.sleep(0.01)
        duration = self.telemetry.stop_timer(timer_name)
        self.assertGreater(duration, 0.0)

        # Stop non-existent timer should not crash
        fallback_duration = self.telemetry.stop_timer(uuid.uuid4().hex)
        self.assertGreaterEqual(fallback_duration, 0.0)

    def test_check_system_health(self):
        mock_psutil = unittest.mock.MagicMock()
        cpu_val = random.uniform(0.0, 100.0)
        mem_val = random.uniform(0.0, 100.0)
        mock_psutil.cpu_percent.return_value = cpu_val
        mock_psutil.virtual_memory.return_value.percent = mem_val

        with patch("skills.system_telemetry.psutil", mock_psutil):
            health = self.telemetry.check_system_health()
            self.assertEqual(health["cpu_usage"], cpu_val)
            self.assertEqual(health["memory_usage"], mem_val)

    def test_psutil_missing_fallback(self):
        with patch("skills.system_telemetry.psutil", None):
            metrics = self.telemetry.collect_system_metrics()
            self.assertEqual(metrics["cpu_usage"], 0.0)
            self.assertEqual(metrics["memory_usage"], 0.0)

            health = self.telemetry.monitor_engine_health()
            self.assertEqual(health["cpu_usage"], 0.0)
            self.assertEqual(health["memory_usage"], 0.0)

if __name__ == "__main__":
    unittest.main()