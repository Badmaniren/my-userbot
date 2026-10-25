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
        self.random_metric_key = uuid.uuid4().hex
        self.random_metric_val = random.randint(100, 999)
        self.random_text = uuid.uuid4().hex
        self.random_ascii = uuid.uuid4().hex

    def test_export_json_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.return_value = {self.random_metric_key: self.random_metric_val}
        mock_visualizer.render_text.return_value = self.random_text
        mock_visualizer.render_ascii_correlation_graph.return_value = self.random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = exporter.export_json_report(self.output_path)
            self.assertEqual(result_path, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")
            
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)
            
            self.assertEqual(parsed_data[self.random_metric_key], self.random_metric_val)
            self.assertEqual(parsed_data["text_report"], self.random_text)
            self.assertEqual(parsed_data["ascii_graph"], self.random_ascii)

    def test_export_json_report_raises_exporter_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        metrics_dict = {uuid.uuid4().hex: random.randint(1, 50)}
        mock_visualizer.get_summary_metrics.return_value = metrics_dict
        mock_visualizer.render_text.return_value = self.random_text
        mock_visualizer.render_ascii_correlation_graph.return_value = self.random_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = exporter.export_html_report(self.html_output_path)
            self.assertEqual(result_path, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            
            self.assertIn(str(metrics_dict), written_content)
            self.assertIn(self.random_text, written_content)
            self.assertIn(self.random_ascii, written_content)

    def test_export_html_report_raises_exporter_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = ValueError(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        mock_digest = unittest.mock.MagicMock()
        stream_payload = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_digest.export_digest_stream.return_value = stream_payload

        exporter = DigestExporter(stability_digest=mock_digest)

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(result_path, self.output_path)
            mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data, stream_payload)

    def test_export_stream_to_json_raises_exporter_error(self):
        mock_digest = unittest.mock.MagicMock()
        mock_digest.export_digest_stream.side_effect = KeyError(uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=mock_digest)

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        digest_data = {uuid.uuid4().hex: random.randint(10, 100)}
        mock_visualizer.digest = digest_data

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = exporter.export_to_json(self.output_path)
            self.assertEqual(result_path, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data, digest_data)

    def test_export_to_json_adapter_empty_fallback(self):
        exporter = DigestExporter(anomaly_visualizer=None)

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = exporter.export_to_json(self.output_path)
            self.assertEqual(result_path, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data, {})

    def test_export_to_html_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        digest_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_visualizer.digest = digest_data

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = exporter.export_to_html(self.html_output_path)
            self.assertEqual(result_path, self.html_output_path)

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.call_args_list)
            self.assertIn(json.dumps(digest_data), written_content)

    def test_export_to_html_adapter_raises_exporter_error(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        with patch("builtins.open", side_effect=PermissionError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()