import unittest
from unittest.mock import patch, MagicMock
import io
import random
import uuid
import string
from skills.system_health_visualizer import SystemHealthVisualizer

class TestSystemHealthVisualizer(unittest.TestCase):

    def setUp(self):
        self.visualizer = SystemHealthVisualizer()
        self.random_metric_name = ''.join(random.choices(string.ascii_lowercase, k=10))
        self.random_metric_value = random.uniform(0.0, 100.0)
        self.random_system_id = uuid.uuid4().hex

    def test_visualize_critical_metrics_success(self):
        metric_data = {
            self.random_metric_name: self.random_metric_value,
            "system_id": self.random_system_id
        }
        
        mock_gateway = MagicMock()
        mock_gateway.fetch_metrics.return_value = metric_data

        with patch("skills.system_health_visualizer.SystemHealthMonitoringGateway", return_value=mock_gateway):
            result = self.visualizer.visualize_critical_metrics(self.random_system_id)
            
        self.assertIn(self.random_metric_name, result)
        self.assertEqual(result[self.random_metric_name], self.random_metric_value)
        self.assertIn("chart_rendering", result)

    def test_build_realtime_status_graph_valid_telemetry(self):
        telemetry_stream = io.BytesIO(f"metric:{self.random_metric_name},val:{self.random_metric_value}".encode('utf-8'))
        
        mock_collector = MagicMock()
        mock_collector.stream_telemetry.return_value = telemetry_stream

        with patch("skills.system_health_visualizer.SystemHealthTelemetryCollector", return_value=mock_collector):
            graph_payload = self.visualizer.build_realtime_status_graph(uuid.uuid4().hex)

        self.assertIsInstance(graph_payload, dict)
        self.assertIn("nodes", graph_payload)
        self.assertIn("edges", graph_payload)
        self.assertTrue(len(graph_payload["nodes"]) > 0)

    def test_visualize_critical_metrics_handles_aggregator_failure(self):
        mock_aggregator = MagicMock()
        mock_aggregator.aggregate.side_effect = RuntimeError(uuid.uuid4().hex)

        with patch("skills.system_health_visualizer.SystemHealthAggregator", return_value=mock_aggregator):
            with self.assertRaises(Exception):
                self.visualizer.visualize_critical_metrics(self.random_system_id)

    def test_build_realtime_status_graph_empty_stream(self):
        empty_stream = io.BytesIO(b"")
        
        mock_collector = MagicMock()
        mock_collector.stream_telemetry.return_value = empty_stream

        with patch("skills.system_health_visualizer.SystemHealthTelemetryCollector", return_value=mock_collector):
            graph_payload = self.visualizer.build_realtime_status_graph(uuid.uuid4().hex)

        self.assertEqual(graph_payload.get("status"), "EMPTY_STREAM")
        self.assertEqual(graph_payload.get("nodes"), [])

if __name__ == '__main__':
    unittest.main()