import unittest
from unittest.mock import patch, mock_open, MagicMock
import uuid
import random
import io
import json

from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.output_path = f"report_{uuid.uuid4().hex}.json"
        self.html_output_path = f"report_{uuid.uuid4().hex}.html"
        self.stream_id = f"stream_{uuid.uuid4().hex}"

        self.mock_digest = MagicMock()
        self.mock_visualizer = MagicMock()

        self.exporter = DigestExporter(
            stability_digest=self.mock_digest,
            anomaly_visualizer=self.mock_visualizer
        )

    def test_export_json_report_success(self):
        random_metric_key = f"metric_{uuid.uuid4().hex}"
        random_metric_val = random.randint(100, 999)
        random_text = f"text_{uuid.uuid4().hex}"
        random_ascii = f"graph_{uuid.uuid4().hex}"

        self.mock_visualizer.get_summary_metrics.return_value = {random_metric_key: random_metric_val}
        self.mock_visualizer.render_text.return_value = random_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_json_report(self.output_path)

            self.assertEqual(result_path, self.output_path)
            mocked_file.assert_called_once_with(self.output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json[random_metric_key], random_metric_val)
            self.assertEqual(parsed_json["text_report"], random_text)
            self.assertEqual(parsed_json["ascii_graph"], random_ascii)

    def test_export_json_report_non_dict_metrics(self):
        self.mock_visualizer.get_summary_metrics.return_value = [random.randint(1, 10)]
        self.mock_visualizer.render_text.return_value = uuid.uuid4().hex
        self.mock_visualizer.render_ascii_correlation_graph.return_value = uuid.uuid4().hex

        with patch("builtins.open", mock_open()) as mocked_file:
            self.exporter.export_json_report(self.output_path)
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)
            self.assertIn("text_report", parsed_json)
            self.assertIn("ascii_graph", parsed_json)

    def test_export_json_report_raises_exporter_error(self):
        random_error_msg = f"err_{uuid.uuid4().hex}"
        self.mock_visualizer.get_summary_metrics.side_effect = Exception(random_error_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(self.output_path)
        self.assertIn(random_error_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        random_metric = f"metric_val_{uuid.uuid4().hex}"
        random_text = f"text_rep_{uuid.uuid4().hex}"
        random_ascii = f"ascii_rep_{uuid.uuid4().hex}"

        self.mock_visualizer.get_summary_metrics.return_value = random_metric
        self.mock_visualizer.render_text.return_value = random_text
        self.mock_visualizer.render_ascii_correlation_graph.return_value = random_ascii

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_html_report(self.html_output_path)

            self.assertEqual(result_path, self.html_output_path)
            mocked_file.assert_called_once_with(self.html_output_path, "w", encoding="utf-8")

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)

            self.assertIn(random_metric, written_data)
            self.assertIn(random_text, written_data)
            self.assertIn(random_ascii, written_data)

    def test_export_html_report_raises_exporter_error(self):
        random_error_msg = f"html_err_{uuid.uuid4().hex}"
        self.mock_visualizer.render_text.side_effect = Exception(random_error_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_html_report(self.html_output_path)
        self.assertIn(random_error_msg, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        random_key = f"key_{uuid.uuid4().hex}"
        random_val = f"val_{uuid.uuid4().hex}"
        stream_payload = {random_key: random_val}

        self.mock_digest.export_digest_stream.return_value = stream_payload

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_stream_to_json(self.stream_id, self.output_path)

            self.assertEqual(result_path, self.output_path)
            self.mock_digest.export_digest_stream.assert_called_once_with(self.stream_id)

            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json[random_key], random_val)

    def test_export_stream_to_json_raises_exporter_error(self):
        random_error_msg = f"stream_err_{uuid.uuid4().hex}"
        self.mock_digest.export_digest_stream.side_effect = Exception(random_error_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_stream_to_json(self.stream_id, self.output_path)
        self.assertIn(random_error_msg, str(ctx.exception))

    def test_export_to_json_adapter_success(self):
        random_key = f"adapter_key_{uuid.uuid4().hex}"
        random_val = random.randint(1, 1000)

        self.mock_visualizer.digest = {random_key: random_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.output_path)

            self.assertEqual(result_path, self.output_path)
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json[random_key], random_val)

    def test_export_to_json_adapter_empty(self):
        self.exporter.visualizer = None

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_json(self.output_path)

            self.assertEqual(result_path, self.output_path)
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)
            parsed_json = json.loads(written_data)

            self.assertEqual(parsed_json, {})

    def test_export_to_html_adapter_success(self):
        random_key = f"html_adapter_key_{uuid.uuid4().hex}"
        random_val = f"html_adapter_val_{uuid.uuid4().hex}"

        self.mock_visualizer.digest = {random_key: random_val}

        with patch("builtins.open", mock_open()) as mocked_file:
            result_path = self.exporter.export_to_html(self.html_output_path)

            self.assertEqual(result_path, self.html_output_path)
            handle = mocked_file()
            written_data = "".join(call.args[0] for call in handle.write.mock_calls)

            self.assertIn(random_key, written_data)
            self.assertIn(random_val, written_data)
            self.assertTrue(written_data.startswith("<html>"))


if __name__ == "__main__":
    unittest.main()