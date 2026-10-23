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
        expected_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        mock_visualizer.get_summary_metrics.return_value = expected_metrics
        mock_visualizer.render_text.return_value = expected_text
        mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_json_report(self.output_path)
            self.assertEqual(result, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_content)

            self.assertEqual(parsed_data["text_report"], expected_text)
            self.assertEqual(parsed_data["ascii_graph"], expected_ascii)

    def test_export_json_report_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        expected_metrics = uuid.uuid4().hex
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        mock_visualizer.get_summary_metrics.return_value = expected_metrics
        mock_visualizer.render_text.return_value = expected_text
        mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_html_report(self.html_output_path)
            self.assertEqual(result, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn(expected_metrics, written_content)
            self.assertIn(expected_text, written_content)
            self.assertIn(expected_ascii, written_content)

    def test_export_html_report_error(self):
        mock_visualizer = unittest.mock.MagicMock()
        mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with self.assertRaises(DigestExporterError):
            exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        mock_digest = unittest.mock.MagicMock()
        expected_stream = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_digest.export_digest_stream.return_value = expected_stream

        exporter = DigestExporter(stability_digest=mock_digest)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(result, self.output_path)
            mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_content)
            self.assertEqual(parsed_data, expected_stream)

    def test_export_stream_to_json_error(self):
        mock_digest = unittest.mock.MagicMock()
        mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        exporter = DigestExporter(stability_digest=mock_digest)

        with self.assertRaises(DigestExporterError):
            exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        expected_digest = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_visualizer.digest = expected_digest

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_to_json(self.output_path)
            self.assertEqual(result, self.output_path)

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_content)
            self.assertEqual(parsed_data, expected_digest)

    def test_export_to_json_adapter_error(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                exporter.export_to_json(self.output_path)

    def test_export_to_html_adapter_success(self):
        mock_visualizer = unittest.mock.MagicMock()
        expected_digest = {uuid.uuid4().hex: uuid.uuid4().hex}
        mock_visualizer.digest = expected_digest

        exporter = DigestExporter(anomaly_visualizer=mock_visualizer)

        with patch("builtins.open", mock_open()) as mocked_file:
            result = exporter.export_to_html(self.html_output_path)
            self.assertEqual(result, self.html_output_path)

            handle = mocked_file()
            written_content = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn(json.dumps(expected_digest), written_content)

    def test_export_to_html_adapter_error(self):
        exporter = DigestExporter(anomaly_visualizer=None)
        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                exporter.export_to_html(self.html_output_path)


if __name__ == "__main__":
    unittest.main()