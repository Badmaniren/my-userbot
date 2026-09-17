import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
import string

from skills.telemetry_anomaly_detector import TelemetryAnomalyDetector


class TestTelemetryAnomalyDetector(unittest.TestCase):

    def setUp(self):
        self.detector = TelemetryAnomalyDetector()

    def test_analyze_stream_spike_detection(self):
        metric_name = ''.join(random.choices(string.ascii_lowercase, k=12))
        normal_value = random.uniform(10.0, 50.0)
        spike_value = random.uniform(500.0, 1000.0)

        telemetry_stream = [
            {"metric": metric_name, "value": normal_value},
            {"metric": metric_name, "value": normal_value * 1.05},
            {"metric": metric_name, "value": spike_value}
        ]

        result = self.detector.analyze(telemetry_stream)

        self.assertIsInstance(result, list)
        self.assertTrue(len(result) > 0)

        detected = False
        for anomaly in result:
            if anomaly.get("metric") == metric_name:
                self.assertEqual(anomaly.get("value"), spike_value)
                self.assertEqual(anomaly.get("status"), "ANOMALY_DETECTED")
                detected = True
                break
        self.assertTrue(detected, "Spike anomaly was not detected by the processor.")

    def test_analyze_empty_stream(self):
        empty_stream = []
        result = self.detector.analyze(empty_stream)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 0)

    def test_process_stream_with_mock_io(self):
        random_id = uuid.uuid4().hex
        metric_key = f"metric_{random_id}"
        metric_val = random.randint(1000, 9999)

        raw_data = f"{metric_key}:{metric_val}\n".encode('utf-8')
        mock_file = io.BytesIO(raw_data)

        with patch('skills.telemetry_anomaly_detector.open', return_value=mock_file):
            result = self.detector.analyze_stream_from_source(uuid.uuid4().hex)

            self.assertIsInstance(result, dict)
            self.assertIn("anomalies", result)

    def test_threshold_adjustment(self):
        custom_threshold = random.uniform(2.0, 5.0)
        self.detector.set_threshold(custom_threshold)

        self.assertEqual(self.detector.threshold, custom_threshold)

        metric_name = uuid.uuid4().hex
        stream = [
            {"metric": metric_name, "value": 10},
            {"metric": metric_name, "value": 15}
        ]

        result = self.detector.analyze(stream)
        self.assertEqual(len(result), 0)


if __name__ == '__main__':
    unittest.main()