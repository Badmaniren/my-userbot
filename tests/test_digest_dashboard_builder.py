import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import json

from skills.digest_dashboard_builder import DigestDashboardBuilder, DigestDashboardBuilderError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter


class TestDigestDashboardBuilder(unittest.TestCase):

    def setUp(self):
        self.random_string_1 = uuid.uuid4().hex
        self.random_string_2 = uuid.uuid4().hex
        self.random_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.json"
        self.random_html_path = f"/tmp/{uuid.uuid4().hex}/{uuid.uuid4().hex}.html"
        self.digest_data = {
            self.random_string_1: random.randint(100, 999),
            self.random_string_2: random.choice(string.ascii_letters)
        }

    @patch('skills.digest_dashboard_builder.DigestExporter')
    @patch('skills.digest_dashboard_builder.AnomalyVisualizer')
    def test_dashboard_builder_initialization_and_composition(self, mock_visualizer_cls, mock_exporter_cls):
        mock_visualizer_instance = mock_visualizer_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value

        builder = DigestDashboardBuilder(self.digest_data)

        mock_visualizer_cls.assert_called_once_with(self.digest_data)
        mock_exporter_cls.assert_called_once_with(
            stability_digest=self.digest_data,
            anomaly_visualizer=mock_visualizer_instance
        )
        self.assertEqual(builder.visualizer, mock_visualizer_instance)
        self.assertEqual(builder.exporter, mock_exporter_instance)

    @patch('skills.digest_dashboard_builder.DigestExporter')
    @patch('skills.digest_dashboard_builder.AnomalyVisualizer')
    def test_build_dashboard_success(self, mock_visualizer_cls, mock_exporter_cls):
        mock_visualizer_instance = mock_visualizer_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value

        expected_rendered_text = f"TEXT_{uuid.uuid4().hex}"
        expected_graph = f"GRAPH_{uuid.uuid4().hex}"
        expected_summary = {uuid.uuid4().hex: random.randint(1, 10)}
        expected_json_path = f"/tmp/{uuid.uuid4().hex}.json"
        expected_html_path = f"/tmp/{uuid.uuid4().hex}.html"

        mock_visualizer_instance.render_text.return_value = expected_rendered_text
        mock_visualizer_instance.render_ascii_correlation_graph.return_value = expected_graph
        mock_visualizer_instance.get_summary_metrics.return_value = expected_summary
        
        mock_exporter_instance.export_to_json.return_value = expected_json_path
        mock_exporter_instance.export_to_html.return_value = expected_html_path

        builder = DigestDashboardBuilder(self.digest_data)
        dashboard = builder.build_dashboard(self.random_path, self.random_html_path)

        mock_visualizer_instance.render_text.assert_called_once()
        mock_visualizer_instance.render_ascii_correlation_graph.assert_called_once()
        mock_visualizer_instance.get_summary_metrics.assert_called_once()
        mock_exporter_instance.export_to_json.assert_called_once_with(self.random_path)
        mock_exporter_instance.export_to_html.assert_called_once_with(self.random_html_path)

        self.assertIn("text_report", dashboard)
        self.assertIn("correlation_graph", dashboard)
        self.assertIn("summary_metrics", dashboard)
        self.assertIn("json_export_path", dashboard)
        self.assertIn("html_export_path", dashboard)

        self.assertEqual(dashboard["text_report"], expected_rendered_text)
        self.assertEqual(dashboard["correlation_graph"], expected_graph)
        self.assertEqual(dashboard["summary_metrics"], expected_summary)
        self.assertEqual(dashboard["json_export_path"], expected_json_path)
        self.assertEqual(dashboard["html_export_path"], expected_html_path)

    @patch('skills.digest_dashboard_builder.DigestExporter')
    @patch('skills.digest_dashboard_builder.AnomalyVisualizer')
    def test_build_dashboard_visualizer_failure_raises_custom_error(self, mock_visualizer_cls, mock_exporter_cls):
        mock_visualizer_instance = mock_visualizer_cls.return_value
        error_message = f"VISUALIZER_FAIL_{uuid.uuid4().hex}"
        mock_visualizer_instance.render_text.side_effect = Exception(error_message)

        builder = DigestDashboardBuilder(self.digest_data)

        with self.assertRaises(DigestDashboardBuilderError) as ctx:
            builder.build_dashboard(self.random_path, self.random_html_path)

        self.assertIn(error_message, str(ctx.exception))

    @patch('skills.digest_dashboard_builder.DigestExporter')
    @patch('skills.digest_dashboard_builder.AnomalyVisualizer')
    def test_build_dashboard_exporter_failure_raises_custom_error(self, mock_visualizer_cls, mock_exporter_cls):
        mock_visualizer_instance = mock_visualizer_cls.return_value
        mock_exporter_instance = mock_exporter_cls.return_value
        
        error_message = f"EXPORTER_FAIL_{uuid.uuid4().hex}"
        mock_exporter_instance.export_to_json.side_effect = Exception(error_message)

        builder = DigestDashboardBuilder(self.digest_data)

        with self.assertRaises(DigestDashboardBuilderError) as ctx:
            builder.build_dashboard(self.random_path, self.random_html_path)

        self.assertIn(error_message, str(ctx.exception))


if __name__ == '__main__':
    unittest.main()