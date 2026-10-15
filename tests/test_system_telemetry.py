import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string

from skills.system_telemetry import SystemTelemetry, SystemTelemetryError


class TestSystemTelemetry(unittest.TestCase):

    def setUp(self):
        self.repo_path = f"/tmp/repo_{uuid.uuid4().hex}"
        self.telemetry = SystemTelemetry(repo_path=self.repo_path)

    def test_initialization_success(self):
        self.assertEqual(self.telemetry.repo_path, self.repo_path)
        self.assertIsInstance(self.telemetry.metrics, dict)

    def test_record_and_get_metric(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        metric_value = random.uniform(1.0, 100.0)
        
        self.telemetry.record_metric(metric_name, metric_value)
        history = self.telemetry.get_metric_history(metric_name)
        
        self.assertIn(metric_value, history)
        self.assertEqual(history[-1], metric_value)

    def test_record_metric_no_silent_suppression(self):
        metric_name = f"metric_{uuid.uuid4().hex[:8]}"
        
        with patch.object(self.telemetry, '_validate_metric', side_effect=Exception(f"Error {uuid.uuid4().hex}")):
            with self.assertRaises((SystemTelemetryError, Exception)):
                self.telemetry.record_metric(metric_name, random.randint(1, 10))

    def test_collect_telemetry_snapshot(self):
        execution_id = uuid.uuid4().hex
        metric_name = f"cpu_load_{uuid.uuid4().hex[:6]}"
        metric_value = random.random() * 100
        
        self.telemetry.record_metric(metric_name, metric_value)
        snapshot = self.telemetry.collect_snapshot(execution_id)
        
        self.assertIsInstance(snapshot, dict)
        self.assertEqual(snapshot.get("execution_id"), execution_id)
        self.assertIn(metric_name, snapshot.get("metrics", {}))

    def test_export_telemetry_stream(self):
        stream_id = uuid.uuid4().hex
        mock_file_data = io.BytesIO(stream_id.encode('utf-8'))
        
        with patch('builtins.open', return_value=mock_file_data) as mock_file:
            result = self.telemetry.export_stream(stream_id)
            self.assertIsNotNone(result)

    def test_telemetry_error_propagation(self):
        bad_metric_name = f"".join(random.choices(string.ascii_letters, k=10))
        
        with patch.dict(self.telemetry.metrics, {bad_metric_name: None}, clear=True):
            with self.assertRaises((SystemTelemetryError, TypeError, KeyError)):
                self.telemetry.get_metric_history(bad_metric_name)


if __name__ == "__main__":
    unittest.main()