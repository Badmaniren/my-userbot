import unittest
from unittest.mock import patch, MagicMock
import uuid
import random
import string
import io
import os

from skills.digest_dashboard_generator import DigestDashboardGenerator, DigestDashboardGeneratorError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.digest_exporter import DigestExporter

class TestDigestDashboardGenerator(unittest.TestCase):

    def setUp(self):
        self.rand_str = lambda: ''.join(random.choices(string.ascii_letters, k=8))
        self.rand_path = f"/tmp/{uuid.uuid4().hex}/{self.rand_str()}.json"
        self.rand_html_path = f"/tmp/{uuid.uuid4().hex}/{self.rand_str()}.html"
        self.digest_data = {
            self.rand_str(): random.randint(1, 100),
            self.rand_str(): self.rand_str()
        }
        self.generator = DigestDashboardGenerator(self.digest_data)

    def test_initialization_composition(self):
        self.assertIsInstance(self.generator.visualizer, AnomalyVisualizer)
        self.assertIsInstance(self.generator.exporter, DigestExporter)

    def test_generate_dashboard_success(self):
        expected_json = f"{uuid.uuid4().hex}.json"
        expected_html = f"{uuid.uuid4().hex}.html"

        with patch.object(DigestExporter, 'export_to_json', return_value=expected_json) as mock_json, \
             patch.object(DigestExporter, 'export_to_html', return_value=expected_html) as mock_html:
            
            result = self.generator.generate_dashboard(self.rand_path, self.rand_html_path)

            mock_json.assert_called_once_with(self.rand_path)
            mock_html.assert_called_once_with(self.rand_html_path)
            
            self.assertIn('json_report', result)
            self.assertIn('html_report', result)
            self.assertEqual(result['json_report'], expected_json)
            self.assertEqual(result['html_report'], expected_html)

    def test_generate_dashboard_exporter_error(self):
        with patch.object(DigestExporter, 'export_to_json', side_effect=Exception(self.rand_str())):
            with self.assertRaises(DigestDashboardGeneratorError):
                self.generator.generate_dashboard(self.rand_path, self.rand_html_path)

    def test_get_metrics_summary(self):
        expected_metrics = {self.rand_str(): random.randint(100, 999)}
        with patch.object(AnomalyVisualizer, 'get_summary_metrics', return_value=expected_metrics) as mock_metrics:
            metrics = self.generator.get_metrics_summary()
            mock_metrics.assert_called_once()
            self.assertEqual(metrics, expected_metrics)

    def test_render_ascii_graph(self):
        expected_graph = f"\n[ASCII GRAPH] {self.rand_str()}\n"
        with patch.object(AnomalyVisualizer, 'render_ascii_correlation_graph', return_value=expected_graph) as mock_graph:
            graph = self.generator.render_ascii_graph()
            mock_graph.assert_called_once()
            self.assertEqual(graph, expected_graph)

    def test_stream_export_integration(self):
        stream_id = uuid.uuid4().hex
        expected_stream_path = f"/tmp/{uuid.uuid4().hex}.json"
        
        with patch.object(DigestExporter, 'export_stream_to_json', return_value=expected_stream_path) as mock_stream:
            res = self.generator.export_stream(stream_id, self.rand_path)
            mock_stream.assert_called_once_with(stream_id, self.rand_path)
            self.assertEqual(res, expected_stream_path)

    def test_io_stream_processing_mock(self):
        dummy_content = self.rand_str().encode('utf-8')
        mock_file = io.BytesIO(dummy_content)
        
        with patch('skills.digest_dashboard_generator.open', return_value=mock_file, create=True):
            with patch.object(DigestExporter, 'export_to_json', return_value=self.rand_path):
                res = self.generator.generate_dashboard(self.rand_path, self.rand_html_path)
                self.assertIsNotNone(res)