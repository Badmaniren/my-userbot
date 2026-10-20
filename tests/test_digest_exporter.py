import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import json
import os
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporterInquisition(unittest.TestCase):
    def setUp(self):
        self.output_path = f"{uuid.uuid4().hex}.json"
        self.html_output_path = f"{uuid.uuid4().hex}.html"
        self.stream_id = uuid.uuid4().hex
        self.mock_digest = MagicMock()
        self.mock_visualizer = MagicMock()
        self.exporter = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=self.mock_visualizer)

    def tearDown(self):
        for path in [self.output_path, self.html_output_path]:
            if os.path.exists(path):
                try:
                    os.remove(path)
                except OSError:
                    pass

    def test_export_json_report_success(self):
        random_metric_key = uuid.uuid4().hex
        random_metric_val = random.randint(100, 999)
        random_text = f"text_{uuid.uuid4().hex}"
        random_ascii = f"ascii_{uuid.uuid4().hex}"

        self.mock_visualizer.get_summary_metrics.return_value = {random_metric_key: random_metric_val}
        self.mock_visualizer.render_text.return_value = random_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = self.exporter.export_json_report(self.output_path)
            self.assertEqual(res_path, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, 'w', encoding='utf-8')

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data.get(random_metric_key), random_metric_val)
            self.assertEqual(parsed_data.get('text_report'), random_text)
            self.assertEqual(parsed_data.get('ascii_graph'), random_ascii)

    def test_export_json_report_non_dict_metrics(self):
        self.mock_visualizer.get_summary_metrics.return_value = [random.randint(1, 10)]
        random_text = uuid.uuid4().hex
        random_ascii = uuid.uuid4().hex
        self.mock_visualizer.render_text.return_value = random_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            self.exporter.export_json_report(self.output_path)
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_data)

            self.assertEqual(parsed_data.get('text_report'), random_text)
            self.assertEqual(parsed_data.get('ascii_graph'), random_ascii)

    def test_export_json_report_raises_exporter_error(self):
        self.mock_visualizer.get_summary_metrics.side_effect = RuntimeError(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_json_report(self.output_path)

    def test_export_html_report_success(self):
        random_metrics_str = uuid.uuid4().hex
        random_text = uuid.uuid4().hex
        random_ascii = uuid.uuid4().hex

        self.mock_visualizer.get_summary_metrics.return_value = random_metrics_str
        self.mock_visualizer.render_text.return_value = random_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = self.exporter.export_html_report(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, 'w', encoding='utf-8')

            handle = mocked_file()
            written_html = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn(random_metrics_str, written_html)
            self.assertIn(random_text, written_html)
            self.assertIn(random_ascii, written_html)
            self.assertIn("<html>", written_html)

    def test_export_html_report_raises_exporter_error(self):
        self.mock_visualizer.render_text.side_effect = ValueError(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_html_report(self.html_output_path)

    def test_export_stream_to_json_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        stream_payload = {random_key: random_val}
        self.mock_digest.export_digest_stream.return_value = stream_payload

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)
            self.assertEqual(res_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data.get(random_key), random_val)

    def test_export_stream_to_json_raises_exporter_error(self):
        self.mock_digest.export_digest_stream.side_effect = KeyError(uuid.uuid4().hex)
        with self.assertRaises(DigestExporterError):
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)

    def test_export_to_json_adapter_success(self):
        random_key = uuid.uuid4().hex
        random_val = random.randint(1000, 9999)
        self.mock_visualizer.digest = {random_key: random_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = self.exporter.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data.get(random_key), random_val)

    def test_export_to_json_adapter_empty(self):
        exporter_no_vis = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter_no_vis.export_to_json(self.output_path)
            self.assertEqual(res_path, self.output_path)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_data = json.loads(written_data)
            self.assertEqual(parsed_data, {})

    def test_export_to_html_adapter_success(self):
        random_key = uuid.uuid4().hex
        random_val = uuid.uuid4().hex
        self.mock_visualizer.digest = {random_key: random_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = self.exporter.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

            handle = mocked_file()
            written_html = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn(random_key, written_html)
            self.assertIn(random_val, written_html)
            self.assertIn("<html><body><pre>", written_html)

    def test_export_to_html_adapter_empty(self):
        exporter_no_vis = DigestExporter(stability_digest=self.mock_digest, anomaly_visualizer=None)
        with patch("builtins.open", mock_open()) as mocked_file:
            res_path = exporter_no_vis.export_to_html(self.html_output_path)
            self.assertEqual(res_path, self.html_output_path)

            handle = mocked_file()
            written_html = "".join(call.args[0] for call in handle.write.mock_calls)
            self.assertIn("{}", written_html)