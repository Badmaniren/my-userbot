import unittest
import uuid
import random
from skills.telemetry_anomaly_evaluator import telemetry_anomaly_evaluator
from skills import telemetry_processor
from skills import incident_aggregator

class TestTelemetryAnomalyEvaluatorIntegration(unittest.TestCase):
    def test_evaluate_stream_integration_flow(self):
        unique_stream_id = f"stream-{uuid.uuid4()}"
        metrics = ["CPU_LOAD", "MEMORY_USAGE", "LATENCY_MS", "ERROR_RATE"]
        selected_metric = random.choice(metrics)

        threshold = round(random.uniform(50.0, 90.0), 2)
        anomaly_value = round(threshold + random.uniform(10.0, 50.0), 2)

        raw_stream_data = f"STREAM_ID: {unique_stream_id}; METRIC: {selected_metric}; VALUE: {anomaly_value}"

        processed_stream = telemetry_processor.process(raw_stream_data) if hasattr(telemetry_processor, 'process') else raw_stream_data

        result = telemetry_anomaly_evaluator.evaluate_stream(processed_stream, threshold)

        self.assertTrue(result.get('anomaly_detected'), "Anomaly must be detected when value exceeds threshold")
        self.assertEqual(result.get('stream_id'), unique_stream_id)
        self.assertEqual(result.get('metric'), selected_metric)
        self.assertEqual(result.get('metric_value'), anomaly_value)
        self.assertTrue(result.get('incident_metric_feed'))

    def test_callable_payload_integration(self):
        unique_stream_id = f"stream-{uuid.uuid4()}"
        selected_metric = f"metric-{uuid.uuid4().hex[:6]}"
        threshold = 100.0
        normal_value = round(random.uniform(10.0, 90.0), 2)

        payload = {
            "processed_stream": {
                "stream_id": unique_stream_id,
                "metric_name": selected_metric,
                "value": normal_value
            },
            "threshold": threshold
        }

        result = telemetry_anomaly_evaluator(payload)

        self.assertFalse(result.get('anomaly_detected'), "Anomaly should not be detected below threshold")
        self.assertEqual(result.get('stream_id'), unique_stream_id)
        self.assertEqual(result.get('metric'), selected_metric)
        self.assertEqual(result.get('metric_value'), normal_value)
        self.assertFalse(result.get('incident_metric_feed'))

if __name__ == '__main__':
    unittest.main()