import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import os
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex

        self.mock_digest = MagicMock()
        self.mock_visualizer = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def tearDown(self):
        for path in [self.output_path, self.html_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_success(self):
        expected_metrics = {uuid.uuid4().hex: random.randint(1, 100)}
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = expected_metrics
        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_json_report(self.output_path)

            self.assertEqual(res_path, self.output_path)
            mock_file.assert_called_once_with(self.output_path, 'w', encoding='utf-8')

            handle = mock_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data['text_report'], expected_text)
            self.assertEqual(parsed_data['ascii_graph'], expected_ascii)

    def test_export_json_report_exception(self):
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        expected_metrics = uuid.uuid4().hex
        expected_text = uuid.uuid4().hex
        expected_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = expected_metrics
        self.mock_visualizer.render_text.return_value = expected_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = expected_ascii

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_html_report(self.html_output_path)

            self.assertEqual(res_path, self.html_output_path)
            mock_file.assert_called_once_with(self.html_output_path, 'w', encoding='utf-8')

            handle = mock_file()
            html_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn(expected_metrics, html_content)
            self.assertIn(expected_text, html_content)
            self.assertIn(expected_ascii, html_content)

    def test_export_html_report_exception(self):
        self.mock_visualizer.render_text.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        expected_stream_data = {uuid.uuid4().hex: uuid.uuid4().hex}
        self.mock_digest.export_digest_stream.return_value = expected_stream_data

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)

            self.assertEqual(res_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mock_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data, expected_stream_data)

    def test_export_stream_to_json_exception(self):
        self.mock_digest.export_digest_stream.side_effect = Exception(uuid.uuid4().hex)

        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        expected_key = uuid.uuid4().hex
        expected_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {expected_key: expected_val}

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)

            self.assertEqual(res_path, self.output_path)
            handle = mock_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data[expected_key], expected_val)

    def test_export_to_json_adapter_empty(self):
        self.exporter.visualizer = None

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_json(self.output_path)

            self.assertEqual(res_path, self.output_path)
            handle = mock_file()
            written_data = "".join(call.args[0] for call in handle.write.call_args_list)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data, {})

    def test_export_to_json_adapter_exception(self):
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_json(self.output_path)

    def test_export_to_html_adapter_success(self):
        expected_key = uuid.uuid4().hex
        expected_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {expected_key: expected_val}

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_html(self.html_output_path)

            self.assertEqual(res_path, self.html_output_path)
            handle = mock_file()
            html_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn(expected_key, html_content)
            self.assertIn(expected_val, html_content)

    def test_export_to_html_adapter_empty(self):
        self.exporter.visualizer = None

        with patch("builtins.open", unittest.mock.mock_open()) as mock_file:
            res_path = self.exporter.export_to_html(self.html_output_path)

            self.assertEqual(res_path, self.html_output_path)
            handle = mock_file()
            html_content = "".join(call.args[0] for call in handle.write.call_args_list)

            self.assertIn("<html>", html_content)

    def test_export_to_html_adapter_exception(self):
        with patch("builtins.open", side_effect=Exception(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(self.html_output_path)


if __name__ == '__main__':
    unittest.main()