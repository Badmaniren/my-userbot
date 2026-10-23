import unittest
from unittest.mock import patch, mock_open
import uuid
import random
import json
import io

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

    def test_export_json_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 1000)
        mock_visualizer.get_summary_metrics.return_value = {rand_metric_key: rand_metric_val}

        rand_text = uuid.uuid4().hex
        mock_visualizer.render_text.return_value = rand_text

        rand_ascii = uuid.uuid4().hex
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_json_report(self.output_path)
            self.assertEqual(result, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_metric_key], rand_metric_val)
            self.assertEqual(parsed_json["text_report"], rand_text)
            self.assertEqual(parsed_json["ascii_graph"], rand_ascii)

    def test_export_json_report_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_metric_key = uuid.uuid4().hex
        mock_visualizer.get_summary_metrics.return_value = {rand_metric_key: random.randint(10, 500)}
        rand_text = uuid.uuid4().hex
        mock_visualizer.render_text.return_value = rand_text
        rand_ascii = uuid.uuid4().hex
        mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_html_report(self.html_output_path)
            self.assertEqual(result, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_html = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn("<html>", written_html)
            self.assertIn(rand_text, written_html)
            self.assertIn(rand_ascii, written_html)

    def test_export_html_report_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        mock_digest = unittest.mock.MagicMock()
        rand_stream_key = uuid.uuid4().hex
        rand_stream_val = uuid.uuid4().hex
        mock_digest.export_digest_stream.return_value = {rand_stream_key: rand_stream_val}

        exporter = DigestExporter(stability_digest=mock_digest, anomaly_visualizer=None)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(result, self.output_path)
            mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_stream_key], rand_stream_val)

    def test_export_stream_to_json_error(self):
        mock_digest = unittest.mock.MagicMock()
        mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=mock_digest, anomaly_visualizer=None)

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_visualizer.digest = {rand_key: rand_val}

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_to_json(self.output_path)
            self.assertEqual(result, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_key], rand_val)

    def test_export_to_json_adapter_no_digest(self):
        mock_visualizer = unittest.mock.MagicMock(spec=[])

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_to_json(self.output_path)
            self.assertEqual(result, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json, {})

    def test_export_to_html_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        mock_visualizer.digest = {rand_key: rand_val}

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_to_html(self.html_output_path)
            self.assertEqual(result, self.html_output_path)

            handle = mocked_file()
            written_html = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn(rand_key, written_html)
            self.assertIn(rand_val, written_html)

    def test_export_to_html_adapter_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        type(mock_visualizer).digest = unittest.mock.PropertyMock(side_effect=Exception(uuid.uuid4().hex))

        exporter = DigestExporter(stability_digest=None, anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_to_html(self.html_output_path)