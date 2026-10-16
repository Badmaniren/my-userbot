import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import io
import string

from skills.digest_dashboard_aggregator import DigestDashboardAggregator
from skills.anomaly_visualizer import AnomalyVisualizer, AnomalyVisualizerError
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestDashboardAggregator(unittest.TestCase):

    def setUp(self):
        self.random_digest_data = {
            "id": uuid.uuid4().hex,
            "metric": random.randint(100, 999),
            "status": random.choice(["OK", "WARNING", "CRITICAL"])
        }
        self.random_file_path = f"/tmp/{uuid.uuid4().hex}.json"
        self.random_output_path = f"/tmp/{uuid.uuid4().hex}.html"
        self.random_stream_id = uuid.uuid4().hex

    def test_aggregator_initialization_and_composition(self):
        mock_visualizer = MagicMock(spec=AnomalyVisualizer)
        mock_exporter = MagicMock(spec=DigestExporter)

        with patch('skills.digest_dashboard_aggregator.omaly_visualizer', create=True):
            aggregator = DigestDashboardAggregator(
                anomaly_visualizer=mock_visualizer,
                digest_exporter=mock_exporter
            )

            self.assertEqual(aggregator.visualizer, mock_visualizer)
            self.assertEqual(aggregator.exporter, mock_exporter)

    def test_aggregate_dashboard_data_success(self):
        mock_visualizer = MagicMock(spec=AnomalyVisualizer)
        expected_summary = {
            uuid.uuid4().hex: random.randint(1, 100),
            "status": random.choice(["stable", "unstable"])
        }
        mock_visualizer.get_summary_metrics.return_value = expected_summary
        mock_visualizer.render_text.return_value = uuid.uuid4().hex

        mock_exporter = MagicMock(spec=DigestExporter)
        expected_export_path = f"/var/log/{uuid.uuid4().hex}.json"
        mock_exporter.export_to_json.return_value = expected_export_path

        aggregator = DigestDashboardAggregator(
            anomaly_visualizer=mock_visualizer,
            digest_exporter=mock_exporter
        )

        result = aggregator.aggregate_dashboard_data(self.random_output_path)

        mock_visualizer.get_summary_metrics.assert_called_once()
        mock_exporter.export_to_json.assert_called_once_with(self.random_output_path)

        self.assertIn("metrics", result)
        self.assertIn("export_path", result)
        self.assertEqual(result["metrics"], expected_summary)
        self.assertEqual(result["export_path"], expected_export_path)

    def test_aggregate_dashboard_data_visualizer_error(self):
        mock_visualizer = MagicMock(spec=AnomalyVisualizer)
        error_message = uuid.uuid4().hex
        mock_visualizer.get_summary_metrics.side_effect = AnomalyVisualizerError(error_message)

        mock_exporter = MagicMock(spec=DigestExporter)

        aggregator = DigestDashboardAggregator(
            anomaly_visualizer=mock_visualizer,
            digest_exporter=mock_exporter
        )

        with self.assertRaises(AnomalyVisualizerError):
            aggregator.aggregate_dashboard_data(self.random_output_path)

    def test_aggregate_dashboard_data_exporter_error(self):
        mock_visualizer = MagicMock(spec=AnomalyVisualizer)
        mock_visualizer.get_summary_metrics.return_value = {uuid.uuid4().hex: random.random()}

        mock_exporter = MagicMock(spec=DigestExporter)
        error_message = uuid.uuid4().hex
        mock_exporter.export_to_json.side_effect = DigestExporterError(error_message)
        mock_exporter.export_to_html.side_effect = DigestExporterError(error_message)

        aggregator = DigestDashboardAggregator(
            anomaly_visualizer=mock_visualizer,
            digest_exporter=mock_exporter
        )

        with self.assertRaises(DigestExporterError):
            aggregator.aggregate_dashboard_data(self.random_output_path)

    def test_render_full_dashboard_stream(self):
        mock_visualizer = MagicMock(spec=AnomalyVisualizer)
        ascii_graph = f"GRAPH-{uuid.uuid4().hex}"
        mock_visualizer.render_ascii_correlation_graph.return_value = ascii_graph

        mock_exporter = MagicMock(spec=DigestExporter)
        stream_path = f"/tmp/{uuid.uuid4().hex}.stream"
        mock_exporter.export_stream_to_json.return_value = stream_path

        aggregator = DigestDashboardAggregator(
            anomaly_visualizer=mock_visualizer,
            digest_exporter=mock_exporter
        )

        result = aggregator.render_full_dashboard_stream(self.random_stream_id, stream_path)

        mock_visualizer.render_ascii_correlation_graph.assert_called_once()
        mock_exporter.export_stream_to_json.assert_called_once_with(self.random_stream_id, stream_path)

        self.assertEqual(result["ascii_graph"], ascii_graph)
        self.assertEqual(result["stream_file"], stream_path)


if __name__ == '__main__':
    unittest.main()