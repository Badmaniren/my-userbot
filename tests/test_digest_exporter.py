import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import json
import io

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterUnit(unittest.TestCase):

    def setUp(self):
        self.random_path = f"{uuid.uuid4().hex}.json"
        self.random_html_path = f"{uuid.uuid4().hex}.html"
        self.random_stream_id = uuid.uuid4().hex
        self.random_text = uuid.uuid4().hex
        self.random_ascii = uuid.uuid4().hex
        self.random_metric_key = uuid.uuid4().hex
        self.random_metric_value = random.randint(1, 1000)

        self.mock_digest = MagicMock()
        self.mock_visualizer = MagicMock()

        self.mock_visualizer.get_summary_metrics.return_value = {
            self.random_metric_key: self.random_metric_value
        }
        self.mock_visualizer.render_text.return_value = self.random_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = self.random_ascii

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def test_export_json_report_success(self):
        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_json_report(self.random_path)

            self.assertEqual(result_path, self.random_path)
            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json[self.random_metric_key], self.random_metric_value)
            self.assertEqual(parsed_json['text_report'], self.random_text)
            self.assertEqual(parsed_json['ascii_graph'], self.random_ascii)

    def test_export_json_report_raises_custom_exception(self):
        self.mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)

        with patch("builtins.open", mock_open()):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_json_report(self.random_path)

    def test_export_html_report_success(self):
        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_html_report(self.random_html_path)

            self.assertEqual(result_path, self.random_html_path)
            mocked_file.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)

            self.assertIn(self.random_text, written_data)
            self.assertIn(self.random_ascii, written_data)
            self.assertIn(str(self.random_metric_value), written_data)

    def test_export_html_report_raises_custom_exception(self):
        self.mock_visualizer.render_text.side_effect = ValueError(uuid.uuid4().hex)

        with patch("builtins.open", mock_open()):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_html_report(self.random_html_path)

    def test_export_stream_to_json_success(self):
        expected_stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.export_digest_stream.return_value = expected_stream_data

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_stream_to_json(self.random_stream_id, self.random_path)

            self.assertEqual(result_path, self.random_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.random_stream_id)

            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

    def test_export_stream_to_json_raises_custom_exception(self):
        self.mock_digest.export_digest_stream.side_effect = KeyError(uuid.uuid4().hex)

        with patch("builtins.open", mock_open()):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_stream_to_json(self.random_stream_id, self.random_path)

    def test_export_to_json_adapter_success(self):
        adapter_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = adapter_data

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.random_path)

            self.assertEqual(result_path, self.random_path)
            mocked_file.assert_called_once_with(self.random_path, 'w', encoding='utf-8')

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json, adapter_data)

    def test_export_to_json_adapter_raises_custom_exception(self):
        del self.mock_visualizer.digest
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.random_path)

    def test_export_to_html_adapter_success(self):
        adapter_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_visualizer.digest = adapter_data

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_html(self.random_html_path)

            self.assertEqual(result_path, self.random_html_path)
            mocked_file.assert_called_once_with(self.random_html_path, 'w', encoding='utf-8')

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)

            self.assertIn(json.dumps(adapter_data), written_data)

    def test_export_to_html_adapter_raises_custom_exception(self):
        self.mock_visualizer.digest = None
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.random_html_path)

    def test_already_digest_exporter_error_passes_through(self):
        custom_error_msg = uuid.uuid4().hex
        self.mock_visualizer.get_summary_metrics.side_effect = DigestExporterError(custom_error_msg)

        with patch("builtins.open", mock_open()):
            with self.assertRaises(DigestExporterError) as ctx:
                self.exporter.export_json_report(self.random_path)
            self.assertEqual(str(ctx.exception), custom_error_msg)