import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import time
import os

from skills.system_telemetry_collector import SystemTelemetryCollector


class TestSystemTelemetryCollector(unittest.TestCase):
    def setUp(self):
        self.collector = SystemTelemetryCollector()
        self.random_module = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_incident = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=8))
        self.random_metric_value = random.uniform(0.0, 100.0)

    def test_collect_metrics_success(self):
        metrics = self.collector.collect_metrics(self.random_module)
        self.assertIsInstance(metrics, dict)
        self.assertIn("cpu_usage", metrics)
        self.assertIn("memory_usage", metrics)
        self.assertIn("timestamp", metrics)

    def test_record_custom_metric(self):
        self.collector.record_metric(self.random_module, self.random_metric_name, self.random_metric_value)
        history = self.collector.get_metric_history(self.random_module, self.random_metric_name)
        self.assertIsInstance(history, list)
        self.assertTrue(any(val == self.random_metric_value for val in history))

    def test_capture_execution_logs(self):
        log_message = ''.join(random.choices(string.ascii_letters + string.digits, k=32))
        severity = random.choice(["INFO", "DEBUG", "WARNING", "ERROR", "CRITICAL"])

        self.collector.log_execution(self.random_module, severity, log_message)
        logs = self.collector.get_execution_logs(self.random_module)

        self.assertIsInstance(logs, list)
        found = False
        for log in logs:
            if log.get("message") == log_message and log.get("severity") == severity:
                found = True
                break
        self.assertTrue(found, "Записанный лог не найден в истории телеметрии")

    def test_stream_telemetry_data(self):
        stream_data = f"INCIDENT_{self.random_incident}:{random.randint(100, 999)}".encode('utf-8')
        mock_stream = io.BytesIO(stream_data)

        result = self.collector.process_telemetry_stream(self.random_module, mock_stream)
        self.assertTrue(result)

        logs = self.collector.get_execution_logs(self.random_module)
        self.assertTrue(any(self.random_incident in str(l) for l in logs))

    def test_export_telemetry_payload(self):
        self.collector.record_metric(self.random_module, self.random_metric_name, self.random_metric_value)
        payload = self.collector.export_telemetry(self.random_module)

        self.assertIsInstance(payload, dict)
        self.assertEqual(payload.get("module_name"), self.random_module)
        self.assertIn("metrics", payload)
        self.assertIn("logs", payload)

    @patch("time.time")
    def test_metric_timestamp_generation(self, mock_time):
        fake_timestamp = random.randint(1000000000, 2000000000)
        mock_time.return_value = fake_timestamp

        metrics = self.collector.collect_metrics(self.random_module)
        self.assertEqual(metrics.get("timestamp"), fake_timestamp)

    def test_clear_telemetry_history(self):
        self.collector.record_metric(self.random_module, self.random_metric_name, self.random_metric_value)
        self.collector.log_execution(self.random_module, "INFO", uuid.uuid4().hex)

        cleared = self.collector.clear_telemetry(self.random_module)
        self.assertTrue(cleared)

        history = self.collector.get_metric_history(self.random_module, self.random_metric_name)
        logs = self.collector.get_execution_logs(self.random_module)

        self.assertEqual(len(history), 0)
        self.assertEqual(len(logs), 0)


if __name__ == "__main__":
    unittest.main()