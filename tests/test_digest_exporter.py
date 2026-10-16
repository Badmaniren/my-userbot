import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import random
import os
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.anomaly_visualizer import AnomalyVisualizer
from skills.stability_digest import StabilityDigest


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"report_{uuid.uuid4().hex}.json"
        self.html_output_path = f"report_{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        
        self.mock_digest = {uuid.uuid4().hex: random.randint(1, 100)}
        self.stability_digest_instance = MagicMock(spec=StabilityDigest)
        self.stability_digest_instance.export_digest_stream.return_value = self.mock_digest

        self.anomaly_visualizer_instance = MagicMock(spec=AnomalyVisualizer)
        self.anomaly_visualizer_instance.digest = self.mock_digest
        self.anomaly_visualizer_instance.get_summary_metrics.return_value = {"metric": random.randint(10, 50)}
        self.anomaly_visualizer_instance.render_text.return_value = f"text_{uuid.uuid4().hex}"
        self.anomaly_visualizer_instance.render_ascii_correlation_graph.return_value = f"graph_{uuid.uuid4().hex}"

        self.exporter = DigestExporter(
            stability_digest=self.stability_digest_instance,
            anomaly_visualizer=self.anomaly_visualizer_instance
        )

    def tearDown(self):
        for path in [self.output_path, self.html_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_digest_exporter_initialization(self):
        exporter = DigestExporter(
            stability_digest=self.stability_digest_instance,
            anomaly_visualizer=self.anomaly_visualizer_instance
        )
        self.assertEqual(exporter.digest, self.stability_digest_instance)
        self.assertEqual(exporter.visualizer, self.anomaly_visualizer_instance)

    def test_export_json_report_success(self):
        result_path = self.exporter.export_json_report(self.output_path)
        self.assertEqual(result_path, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))
        
        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertIn('text_report', data)
        self.assertIn('ascii_graph', data)
        self.assertEqual(data['text_report'], self.anomaly_visualizer_instance.render_text.return_value)
        self.assertEqual(data['ascii_graph'], self.anomaly_visualizer_instance.render_ascii_correlation_graph.return_value)

    def test_export_html_report_success(self):
        result_path = self.exporter.export_html_report(self.html_output_path)
        self.assertEqual(result_path, self.html_output_path)
        self.assertTrue(os.path.exists(self.html_output_path))
        
        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn("<html>", content)
        self.assertIn(self.anomaly_visualizer_instance.render_text.return_value, content)
        self.assertIn(self.anomaly_visualizer_instance.render_ascii_correlation_graph.return_value, content)

    def test_export_stream_to_json_success(self):
        result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
        self.assertEqual(result_path, self.output_path)
        self.stability_digest_instance.export_digest_stream.assert_called_once_with(self.stream_id)
        
        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertEqual(data, self.mock_digest)

    def test_export_to_json_adapter_success(self):
        result_path = self.exporter.export_to_json(self.output_path)
        self.assertEqual(result_path, self.output_path)
        
        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        self.assertEqual(data, self.mock_digest)

    def test_export_to_html_adapter_success(self):
        result_path = self.exporter.export_to_html(self.html_output_path)
        self.assertEqual(result_path, self.html_output_path)
        
        with open(self.html_output_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        self.assertIn(json.dumps(self.mock_digest), content)

    def test_export_json_report_raises_exception(self):
        self.anomaly_visualizer_instance.get_summary_metrics.side_effect = Exception(f"err_{uuid.uuid4().hex}")
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_raises_exception(self):
        self.anomaly_visualizer_instance.render_text.side_effect = Exception(f"err_{uuid.uuid4().hex}")
        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_raises_exception(self):
        self.stability_digest_instance.export_digest_stream.side_effect = Exception(f"err_{uuid.uuid4().hex}")
        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_raises_exception(self):
        with patch('builtins.open', side_effect=IOError(f"err_{uuid.uuid4().hex}")):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.output_path)

    def test_export_to_html_raises_exception(self):
        with patch('builtins.open', side_effect=IOError(f"err_{uuid.uuid4().hex}")):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)


if __name__ == '__main__':
    unittest.main()