import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
import uuid
import random
import io
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.rand_str_1 = uuid.uuid4().hex
        self.rand_str_2 = uuid.uuid4().hex
        self.rand_str_3 = uuid.uuid4().hex
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_stability_digest = MagicMock()
        self.mock_anomaly_visualizer = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_stability_digest,
            anomaly_visualizer=self.mock_anomaly_visualizer
        )

    def test_export_json_report_success(self):
        expected_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_anomaly_visualizer.get_summary_metrics.return_value = expected_metrics
        self.mock_anomaly_visualizer.render_text.return_value = expected_text
        self.mock_anomaly_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", mock_open()) as mock_file:
            res_path = self.exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)
            mock_file.assert_called_once_with(self.output_path, 'w', encoding='utf-8')

            written_content = "".join(call.args[0] for call in mock_file().write.mock_calls)
            parsed_data = json.loads(written_content)

            self.assertEqual(parsed_data['text_report'], expected_text)
            self.assertEqual(parsed_data['ascii_graph'], expected_ascii)

    def test_export_json_report_exception_handling(self):
        self.mock_anomaly_visualizer.get_summary_metrics.side_effect = Exception(self.rand_str_1)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertIn(self.rand_str_1, str(ctx.exception))

    def test_export_html_report_success(self):
        expected_metrics = {uuid.uuid4().hex: uuid.uuid4().hex}
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_anomaly_visualizer.get_summary_metrics.return_value = expected_metrics
        self.mock_anomaly_visualizer.render_text.return_value = expected_text
        self.mock_anomaly_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", mock_open()) as mock_file:
            res_path = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)
            mock_file.assert_called_once_with(self.html_output_path, 'w', encoding='utf-8')

            written_content = "".join(call.args[0] for call in mock_file().write.mock_calls)
            self.assertIn(expected_text, written_content)
            self.assertIn(expected_ascii, written_content)

    def test_export_html_report_exception_handling(self):
        self.mock_anomaly_visualizer.render_text.side_effect = Exception(self.rand_str_2)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_html_report(self.html_output_path)
        self.assertIn(self.rand_str_2, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        expected_stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_stability_digest.export_digest_stream.return_value = expected_stream_data

        with patch("builtins.open", mock_open()) as mock_file:
            res_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(res_path, self.output_path)
            self.mock_stability_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            written_content = "".join(call.args[0] for call in mock_file().write.mock_calls)
            parsed_data = json.loads(written_content)
            self.assertEqual(parsed_data, expected_stream_data)

    def test_export_stream_to_json_exception_handling(self):
        self.mock_stability_digest.export_digest_stream.side_effect = Exception(self.rand_str_3)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)
        self.assertIn(self.rand_str_3, str(ctx.exception))

    def test_export_to_json_adapter_success(self):
        digest_data = {uuid.uuid4().hex: random.randint(10, 500)}
        self.mock_anomaly_visualizer.digest = digest_data

        with patch("builtins.open", mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

            written_content = "".join(call.args[0] for call in mock_file().write.mock_calls)
            parsed_data = json.loads(written_content)
            self.assertEqual(parsed_data, digest_data)

    def test_export_to_html_adapter_success(self):
        digest_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_anomaly_visualizer.digest = digest_data

        with patch("builtins.open", mock_open()) as mock_file:
            res_path = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

            written_content = "".join(call.args[0] for call in mock_file().write.mock_calls)
            self.assertIn(json.dumps(digest_data), written_content)

    def test_exporter_error_preservation(self):
        original_error = DigestExporterError(self.rand_str_1)
        self.mock_anomaly_visualizer.get_summary_metrics.side_effect = original_error

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertEqual(ctx.exception, original_error)