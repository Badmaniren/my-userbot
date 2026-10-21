import unittest
import json
import uuid
import random
import os
import io
from unittest.mock import patch, MagicMock
from skills.digest_exporter import DigestExporter, DigestExporterError
from skills.stability_digest import StabilityDigest

class TestDigestExporterInquisition(unittest.TestCase):

    def setUp(self) -> None:
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

    def tearDown(self) -> None:
        for path in [self.output_path, self.html_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_success(self) -> None:
        rand_metric_val = random.randint(100, 999)
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = {"metric": rand_metric_val}
        mock_visualizer.render_text.return_value = rand_text
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_json_report(self.output_path)

        self.assertEqual(result_path, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get("metric"), rand_metric_val)
        self.assertEqual(data.get("text_report"), rand_text)
        self.assertEqual(data.get("ascii_graph"), rand_ascii)

    def test_export_json_report_no_visualizer_raises_error(self) -> None:
        exporter = DigestExporter(anomaly_visualizer=None)
        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self) -> None:
        rand_metric_str = uuid.uuid4().hex
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.return_value = rand_metric_str
        mock_visualizer.render_text.return_value = rand_text
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_html_report(self.html_path)

        self.assertEqual(result_path, self.html_path)
        self.assertTrue(os.path.exists(self.html_path))

        with open(self.html_path, 'r', encoding='utf-8') as f:
            content = f.read()

        self.assertIn(rand_text, content)
        self.assertIn(rand_ascii, content)
        self.assertIn("<html>", content)

    def test_export_html_report_no_visualizer_raises_error(self) -> None:
        exporter = DigestExporter(anomaly_visualizer=None)
        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.html_path)

    def test_export_stream_to_json_success(self) -> None:
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        stream_payload = {rand_key: rand_val}

        mock_digest = MagicMock()
        mock_digest.export_digest_stream.return_value = stream_payload

        exporter = DigestExporter(stability_digest=mock_digest)
        result_path = exporter.export_stream_to_json(self.stream_id, self.output_path)

        self.assertEqual(result_path, self.output_path)
        self.assertTrue(os.path.exists(self.output_path))

        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        self.assertEqual(data.get(rand_key), rand_val)
        mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

    def test_export_stream_to_json_no_digest_raises_error(self) -> None:
        exporter = DigestExporter(stability_digest=None)
        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_via_visualizer_digest(self) -> None:
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        mock_visualizer = MagicMock()
        mock_visualizer.digest = {rand_key: rand_val}

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data.get(rand_key), rand_val)

    def test_export_to_json_via_stability_digest(self) -> None:
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        mock_digest = MagicMock()
        mock_digest.digest = {rand_key: rand_val}

        exporter = DigestExporter(stability_digest=mock_digest)
        result_path = exporter.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data.get(rand_key), rand_val)

    def test_export_to_json_fallback_empty(self) -> None:
        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=None)
        result_path = exporter.export_to_json(self.output_path)

        self.assertEqual(result_path, self.output_path)
        with open(self.output_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        self.assertEqual(data, {})

    def test_export_to_html_via_adapters(self) -> None:
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        mock_visualizer = MagicMock()
        mock_visualizer.digest = {rand_key: rand_val}

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        result_path = exporter.export_to_html(self.html_path)

        self.assertEqual(result_path, self.html_path)
        with open(self.html_path, 'r', encoding='utf-8') as f:
            content = f.read()
        self.assertIn(rand_key, content)
        self.assertIn(rand_val, content)
        self.assertIn("<html>", content)

    def test_exporter_exception_handling_wrapper(self) -> None:
        mock_visualizer = MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)
        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_path)