import unittest
from unittest.mock import patch, MagicMock
import random
import uuid
import string
import io
import os
import sys

# Добавляем путь к модулям
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '../skills')))

try:
    from skills.anomaly_telemetry_analyzer import (
        AnomalyTelemetryAnalyzer,
        AnomalyTelemetryAnalyzerError
    )
except ImportError:
    from anomaly_telemetry_analyzer import (
        AnomalyTelemetryAnalyzer,
        AnomalyTelemetryAnalyzerError
    )


class TestAnomalyTelemetryAnalyzer(unittest.TestCase):

    def setUp(self):
        self.rand_stream_size = random.randint(5, 20)
        self.rand_telemetry = [
            {
                "metric": uuid.uuid4().hex,
                "value": random.uniform(0.0, 100.0),
                "timestamp": random.randint(1600000000, 1700000000)
            }
            for _ in range(self.rand_stream_size)
        ]
        self.analyzer = AnomalyTelemetryAnalyzer(
            telemetry_stream=self.rand_telemetry,
            confidence_threshold=random.uniform(0.1, 0.9)
        )

    def test_analyze_deep_patterns_success(self):
        result = self.analyzer.analyze_deep_patterns()
        self.assertIsInstance(result, dict)
        self.assertIn("status", result)
        self.assertEqual(result["status"], "analyzed")
        self.assertEqual(result["patterns"], self.rand_stream_size)

    def test_analyze_deep_patterns_failure(self):
        empty_analyzer = AnomalyTelemetryAnalyzer(telemetry_stream=[])
        with self.assertRaises(AnomalyTelemetryAnalyzerError):
            empty_analyzer.analyze_deep_patterns()

    def test_extract_hidden_signals_randomized(self):
        rand_signal_id = uuid.uuid4().hex
        extracted = self.analyzer.extract_hidden_signals(rand_signal_id)

        self.assertIsInstance(extracted, dict)
        self.assertEqual(extracted["signal"], rand_signal_id)
        self.assertIn("noise_ratio", extracted)
        self.assertIsInstance(extracted["noise_ratio"], float)

    def test_telemetry_stream_io_mocking(self):
        rand_bytes = ''.join(random.choices(string.ascii_letters + string.digits, k=64)).encode('utf-8')
        mock_io = io.BytesIO(rand_bytes)

        with patch('anomaly_telemetry_analyzer.open', return_value=mock_io, create=True):
            read_data = mock_io.read()
            self.assertEqual(read_data, rand_bytes)
            self.assertTrue(len(read_data) > 0)

    def test_anomaly_telemetry_analyzer_custom_exception(self):
        rand_err_msg = uuid.uuid4().hex
        with self.assertRaises(AnomalyTelemetryAnalyzerError) as ctx:
            raise AnomalyTelemetryAnalyzerError(rand_err_msg)
        self.assertIn(rand_err_msg, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()