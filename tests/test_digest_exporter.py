import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import io
import json

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_visualizer = MagicMock()
        self.mock_digest = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def test_export_json_report_success(self):
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(1, 1000)
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = {rand_metric_key: rand_metric_val}
        self.mock_visualizer.render_text.return_value = rand_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_json_report(self.output_path)
            self.assertEqual(result_path, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json[rand_metric_key], rand_metric_val)
            self.assertEqual(parsed_json["text_report"], rand_text)
            self.assertEqual(parsed_json["ascii_graph"], rand_ascii)

    def test_export_json_report_raises_exporter_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        rand_metric = uuid.uuid4().hex
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = rand_metric
        self.mock_visualizer.render_text.return_value = rand_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = rand_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(result_path, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)

            self.assertIn(rand_metric, written_data)
            self.assertIn(rand_text, written_data)
            self.assertIn(rand_ascii, written_data)

    def test_export_html_report_raises_exporter_error(self):
        self.mock_visualizer.render_text.side_effect = ValueError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        rand_stream_key = uuid.uuid4().hex
        rand_stream_val = uuid.uuid4().hex
        stream_data = {rand_stream_key: rand_stream_val}

        self.mock_digest.export_digest_stream.return_value = stream_data

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(result_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_stream_key], rand_stream_val)

    def test_export_stream_to_json_raises_exporter_error(self):
        self.mock_digest.export_digest_stream.side_effect = KeyError(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {rand_key: rand_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(result_path, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_key], rand_val)

    def test_export_to_json_adapter_empty_fallback(self):
        self.exporter.visualizer = None

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(result_path, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json, {})

    def test_export_to_html_adapter_success(self):
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {rand_key: rand_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(result_path, self.html_output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn(rand_key, written_data)
            self.assertIn(rand_val, written_data)


if __name__ == "__main__":
    unittest.main()