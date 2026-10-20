import unittest
from unittest.mock import patch, MagicMock
import json
import uuid
import random
import os
import io

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_json_path = f"{uuid.uuid4().hex}.json"
        self.output_html_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

    def tearDown(self):
        for path in [self.output_json_path, self.output_html_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_success(self):
        mock_visualizer = MagicMock()
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 1000)
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        mock_visualizer.get_summary_metrics.return_value = {rand_metric_key: rand_metric_val}
        mock_visualizer.render_text.return_value = rand_text
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_json_report(self.output_json_path)

        self.assertEqual(result_path, self.output_json_path)
        self.assertTrue(os.path.exists(self.output_json_path))

        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get(rand_metric_key), rand_metric_val)
        self.assertEqual(data.get('text_report'), rand_text)
        self.assertEqual(data.get('ascii_graph'), rand_ascii)

    def test_export_json_report_exception_handling(self):
        mock_visualizer = MagicMock()
        rand_err_msg = uuid.uuid4().hex
        mock_visualizer.get_summary_metrics.side_effect = Exception(rand_err_msg)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_json_report(self.output_json_path)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        mock_visualizer = MagicMock()
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 1000)
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        mock_visualizer.get_summary_metrics.return_value = {rand_metric_key: rand_metric_val}
        mock_visualizer.render_text.return_value = rand_text
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_html_report(self.output_html_path)

        self.assertEqual(result_path, self.output_html_path)
        self.assertTrue(os.path.exists(self.output_html_path))

        with open(self.output_html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(rand_text, content)
        self.assertIn(rand_ascii, content)
        self.assertIn(rand_metric_key, content)

    def test_export_html_report_exception_handling(self):
        mock_visualizer = MagicMock()
        rand_err_msg = uuid.uuid4().hex
        mock_visualizer.render_text.side_effect = Exception(rand_err_msg)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_html_report(self.output_html_path)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        mock_digest = MagicMock()
        rand_stream_key = uuid.uuid4().hex
        rand_stream_val = uuid.uuid4().hex
        mock_digest.export_digest_stream.return_value = {rand_stream_key: rand_stream_val}

        exporter = DigestExporter(stability_digest=mock_digest)
        result_path = exporter.export_stream_to_json(self.stream_id, self.output_json_path)

        self.assertEqual(result_path, self.output_json_path)
        mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get(rand_stream_key), rand_stream_val)

    def test_export_stream_to_json_exception_handling(self):
        mock_digest = MagicMock()
        rand_err_msg = uuid.uuid4().hex
        mock_digest.export_digest_stream.side_effect = Exception(rand_err_msg)

        exporter = DigestExporter(stability_digest=mock_digest)
        with self.assertRaises(DigestExporterError) as ctx:
            exporter.export_stream_to_json(self.stream_id, self.output_json_path)

        self.assertIn(rand_err_msg, str(ctx.exception))

    def test_export_to_json_adapter_success(self):
        mock_visualizer = MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_visualizer.digest = {rand_key: rand_val}

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_to_json(self.output_json_path)

        self.assertEqual(result_path, self.output_json_path)
        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get(rand_key), rand_val)

    def test_export_to_json_adapter_no_digest(self):
        exporter = DigestExporter()
        result_path = exporter.export_to_json(self.output_json_path)

        self.assertEqual(result_path, self.output_json_path)
        with open(self.output_json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data, {})

    def test_export_to_html_adapter_success(self):
        mock_visualizer = MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_visualizer.digest = {rand_key: rand_val}

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_to_html(self.output_html_path)

        self.assertEqual(result_path, self.output_html_path)
        with open(self.output_html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(rand_key, content)
        self.assertIn(rand_val, content)

    def test_export_to_html_adapter_exception_handling(self):
        exporter = DigestExporter()
        with patch('skills.digest_exporter.json.dumps', side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                exporter.export_to_html(self.output_html_path)