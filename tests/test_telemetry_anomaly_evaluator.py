import unittest
from unittest.mock import patch, MagicMock
import io
import uuid
import random
from skills.telemetry_anomaly_evaluator import TelemetryAnomalyEvaluator, telemetry_anomaly_evaluator

class TestTelemetryAnomalyEvaluator(unittest.TestCase):
    def setUp(self):
        self.evaluator = TelemetryAnomalyEvaluator()
        self.stream_id = uuid.uuid4().hex
        self.metric_name = f"metric_{uuid.uuid4().hex[:6]}"

    def test_parse_stream_string(self):
        val = round(random.uniform(50.0, 150.0), 2)
        raw_stream = f"STREAM_ID: {self.stream_id}; METRIC: {self.metric_name}; VALUE: {val}"
        parsed = self.evaluator._parse_stream(raw_stream)
        self.assertEqual(parsed.get('stream_id'), self.stream_id)
        self.assertEqual(parsed.get('metric'), self.metric_name)
        self.assertEqual(parsed.get('value'), val)

    def test_parse_stream_bytes_io(self):
        val = round(random.uniform(1.0, 49.0), 2)
        content = f"stream_id: {self.stream_id}\nmetric: {self.metric_name}\nvalue: {val}".encode('utf-8')
        stream = io.BytesIO(content)
        parsed = self.evaluator._parse_stream(stream)
        self.assertEqual(parsed.get('stream_id'), self.stream_id)
        self.assertEqual(parsed.get('metric'), self.metric_name)
        self.assertEqual(parsed.get('value'), val)

    def test_parse_stream_dict(self):
        val = round(random.uniform(200.0, 500.0), 2)
        payload = {
            "stream_id": self.stream_id,
            "metric": self.metric_name,
            "value": val
        }
        parsed = self.evaluator._parse_stream(payload)
        self.assertEqual(parsed.get('stream_id'), self.stream_id)
        self.assertEqual(parsed.get('metric'), self.metric_name)
        self.assertEqual(parsed.get('value'), val)

    def test_parse_stream_fallback(self):
        weird_stream = 123456789
        parsed = self.evaluator._parse_stream(weird_stream)
        self.assertIsNone(parsed.get('stream_id'))

    def test_evaluate_stream_anomaly(self):
        threshold = 100.0
        val = threshold + random.uniform(10.0, 50.0)
        raw_stream = f"STREAM_ID: {self.stream_id}; METRIC: {self.metric_name}; VALUE: {val}"

        with patch('skills.incident_aggregator.report_anomaly') as mock_report:
            result = self.evaluator.evaluate_stream(raw_stream, threshold)
            self.assertTrue(result['anomaly_detected'])
            self.assertEqual(result['stream_id'], self.stream_id)
            self.assertEqual(result['metric'], self.metric_name)
            self.assertEqual(result['metric_value'], val)
            self.assertEqual(result['breach_value'], val)
            self.assertTrue(result['incident_metric_feed'])
            mock_report.assert_called_once_with(self.stream_id, self.metric_name, val, threshold)

    def test_evaluate_stream_normal(self):
        threshold = 100.0
        val = threshold - random.uniform(1.0, 50.0)
        raw_stream = f"STREAM_ID: {self.stream_id}; METRIC: {self.metric_name}; VALUE: {val}"

        with patch('skills.incident_aggregator.report_anomaly') as mock_report:
            result = self.evaluator.evaluate_stream(raw_stream, threshold)
            self.assertFalse(result['anomaly_detected'])
            self.assertEqual(result['stream_id'], self.stream_id)
            self.assertEqual(result['metric'], self.metric_name)
            self.assertEqual(result['metric_value'], val)
            self.assertNotIn('breach_value', result)
            self.assertNotIn('incident_metric_feed', result)
            mock_report.assert_not_called()

    def test_evaluate_batch(self):
        threshold = 50.0
        val1 = 20.0
        val2 = 80.0
        stream_id_1 = uuid.uuid4().hex
        stream_id_2 = uuid.uuid4().hex

        streams = [
            f"STREAM_ID: {stream_id_1}; METRIC: cpu; VALUE: {val1}",
            f"STREAM_ID: {stream_id_2}; METRIC: mem; VALUE: {val2}"
        ]

        with patch('skills.incident_aggregator.report_anomaly') as mock_report:
            results = self.evaluator.evaluate_batch(streams, threshold)
            self.assertEqual(len(results), 2)
            self.assertFalse(results[0]['anomaly_detected'])
            self.assertTrue(results[1]['anomaly_detected'])
            self.assertEqual(results[1]['stream_id'], stream_id_2)
            mock_report.assert_called_once_with(stream_id_2, 'mem', val2, threshold)

    def test_call_method_anomaly(self):
        threshold = 75.0
        val = 99.9
        payload = {
            "processed_stream": f"STREAM_ID: {self.stream_id}; METRIC: {self.metric_name}; VALUE: {val}",
            "threshold": threshold
        }

        with patch('skills.incident_aggregator.report_anomaly') as mock_report:
            result = telemetry_anomaly_evaluator(payload)
            self.assertTrue(result['anomaly_detected'])
            self.assertTrue(result['incident_metric_feed'])
            self.assertEqual(result['stream_id'], self.stream_id)
            self.assertEqual(result['metric'], self.metric_name)
            self.assertEqual(result['metric_value'], val)
            mock_report.assert_called_once_with(self.stream_id, self.metric_name, val, threshold)

    def test_call_method_default_threshold(self):
        val = 50.0
        payload = {
            "processed_stream": f"STREAM_ID: {self.stream_id}; METRIC: {self.metric_name}; VALUE: {val}"
        }

        with patch('skills.incident_aggregator.report_anomaly') as mock_report:
            result = telemetry_anomaly_evaluator(payload)
            self.assertFalse(result['anomaly_detected'])
            self.assertFalse(result['incident_metric_feed'])
            mock_report.assert_not_called()

if __name__ == '__main__':
    unittest.main()