import unittest
from unittest.mock import MagicMock, patch
import io
import random
import uuid
import string
from skills.market_portfolio_stress_audit_telemetry_aggregator import StressAuditTelemetryAggregator

class TestStressAuditTelemetryAggregator(unittest.TestCase):

    def setUp(self):
        self.aggregator = StressAuditTelemetryAggregator()

    def test_aggregate_stream_data_integrity(self):
        random_stream_id = uuid.uuid4().hex
        random_metric_value = random.uniform(0.01, 999.99)
        random_payload = f'{{"id": "{random_stream_id}", "value": {random_metric_value}}}'.encode('utf-8')

        mock_stream = io.BytesIO(random_payload)

        with patch('skills.market_portfolio_stress_audit_telemetry_aggregator.market_portfolio_stress_audit_realtime_streamer') as mock_streamer:
            mock_streamer.get_stream.return_value = mock_stream

            result = self.aggregator.process_stream(mock_streamer)

            self.assertEqual(result['id'], random_stream_id)
            self.assertEqual(result['value'], random_metric_value)
            self.assertTrue(self.aggregator.is_buffer_flushed())

    def test_filter_anomaly_thresholds(self):
        random_threshold = random.randint(10, 100)
        random_spike = random_threshold + random.randint(1, 50)
        random_normal = random_threshold - random.randint(1, 9)

        self.aggregator.set_threshold(random_threshold)

        self.assertTrue(self.aggregator.should_filter(random_spike))
        self.assertFalse(self.aggregator.should_filter(random_normal))

    def test_accumulation_logic(self):
        random_count = random.randint(5, 20)
        random_metrics = [random.random() for _ in range(random_count)]

        for val in random_metrics:
            self.aggregator.accumulate({'metric': val})

        summary = self.aggregator.get_summary()
        self.assertEqual(len(summary['history']), random_count)
        self.assertEqual(summary['total_processed'], random_count)

    def test_telemetry_export_to_visualizer(self):
        random_visualizer_id = uuid.uuid4().hex
        mock_visualizer = MagicMock()
        mock_visualizer.endpoint_id = random_visualizer_id

        random_data = {'status': ''.join(random.choices(string.ascii_uppercase, k=10))}

        with patch('skills.market_portfolio_stress_audit_telemetry_aggregator.market_portfolio_stress_audit_visualizer') as mock_viz_module:
            mock_viz_module.push.return_value = True

            status = self.aggregator.export_to_visualizer(mock_visualizer, random_data)

            self.assertTrue(status)
            mock_viz_module.push.assert_called_once()
            args, _ = mock_viz_module.push.call_args
            self.assertEqual(args[0], random_visualizer_id)
            self.assertEqual(args[1], random_data)

    def test_invalid_stream_handling(self):
        random_garbage = bytes(''.join(random.choices(string.printable, k=50)), 'utf-8')
        mock_stream = io.BytesIO(random_garbage)

        with patch('skills.market_portfolio_stress_audit_telemetry_aggregator.market_portfolio_stress_audit_realtime_streamer') as mock_streamer:
            mock_streamer.get_stream.return_value = mock_stream

            with self.assertRaises(ValueError):
                self.aggregator.process_stream(mock_streamer)

if __name__ == '__main__':
    unittest.main()