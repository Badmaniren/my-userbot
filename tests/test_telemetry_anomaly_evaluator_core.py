import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import sys
import types

from skills.telemetry_anomaly_evaluator_core import (
    TelemetryAnomalyEvaluatorCore,
    AnomalyEvaluationException,
    InvalidTelemetryStreamException
)

class TestTelemetryAnomalyEvaluatorCore(unittest.TestCase):

    def setUp(self):
        self.evaluator = TelemetryAnomalyEvaluatorCore()
        self.random_stream_id = uuid.uuid4().hex
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        self.random_threshold = random.uniform(10.0, 1000.0)
        self.random_value = self.random_threshold + random.uniform(1.0, 500.0)

    def test_evaluate_anomaly_valid_stream(self):
        telemetry_data = {
            "stream_id": self.random_stream_id,
            "metric": self.random_metric_name,
            "value": self.random_value,
            "threshold": self.random_threshold
        }
        
        result = self.evaluator.evaluate(telemetry_data)
        
        self.assertTrue(result["is_anomaly"])
        self.assertEqual(result["stream_id"], self.random_stream_id)
        self.assertGreater(result["deviation"], 0.0)

    def test_evaluate_anomaly_normal_value(self):
        normal_value = self.random_threshold - random.uniform(0.1, 5.0)
        telemetry_data = {
            "stream_id": self.random_stream_id,
            "metric": self.random_metric_name,
            "value": normal_value,
            "threshold": self.random_threshold
        }
        
        result = self.evaluator.evaluate(telemetry_data)
        
        self.assertFalse(result["is_anomaly"])
        self.assertEqual(result["stream_id"], self.random_stream_id)

    def test_evaluate_invalid_stream_raises_exception(self):
        invalid_data = {
            "stream_id": self.random_stream_id,
            "metric": self.random_metric_name,
            # Missing 'value' and 'threshold' to trigger validation error
        }
        
        with self.assertRaises(InvalidTelemetryStreamException):
            self.evaluator.evaluate(invalid_data)

    def test_evaluate_anomaly_exception_transparency(self):
        telemetry_data = {
            "stream_id": self.random_stream_id,
            "metric": self.random_metric_name,
            "value": self.random_value,
            "threshold": self.random_threshold
        }

        with patch("skills.telemetry_anomaly_evaluator_core.TelemetryAnomalyEvaluatorCore._internal_processor") as mock_processor:
            random_error_msg = uuid.uuid4().hex
            mock_processor.side_effect = RuntimeError(random_error_msg)
            
            with self.assertRaises(AnomalyEvaluationException) as ctx:
                self.evaluator.evaluate(telemetry_data)
            
            self.assertIn(random_error_msg, str(ctx.exception))

    def test_stream_io_processing_with_random_bytes(self):
        random_bytes_content = uuid.uuid4().bytes + os.urandom(16) if 'os' in globals() else uuid.uuid4().bytes
        stream_io = io.BytesIO(random_bytes_content)
        
        with patch("skills.telemetry_anomaly_evaluator_core.TelemetryAnomalyEvaluatorCore._read_stream_bytes") as mock_reader:
            mock_reader.return_value = stream_io
            
            result = self.evaluator.evaluate_stream_source(stream_io)
            self.assertIsNotNone(result)
            self.assertIn("processed_bytes_hash", result)

    def test_incident_trigger_validation_against_threshold(self):
        custom_trigger_id = uuid.uuid4().hex
        telemetry_payload = {
            "stream_id": self.random_stream_id,
            "metric": self.random_metric_name,
            "value": self.random_value * 2,
            "threshold": self.random_threshold,
            "trigger_id": custom_trigger_id
        }

        incident_report = self.evaluator.evaluate_with_incident_trigger(telemetry_payload)
        
        self.assertTrue(incident_report["incident_triggered"])
        self.assertEqual(incident_report["trigger_id"], custom_trigger_id)
        self.assertEqual(incident_report["evaluated_stream"], self.random_stream_id)

if __name__ == '__main__':
    unittest.main()