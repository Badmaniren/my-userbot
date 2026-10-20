import unittest
from unittest.mock import MagicMock, patch
import json
import uuid
import random
import io
from skills.digest_exporter import DigestExporter, DigestExporterError


class TestDigestExporter(unittest.TestCase):

    def setUp(self):
        self.stability_digest_mock = MagicMock()
        self.anomaly_visualizer_mock = MagicMock()
        self.exporter = DigestExporter(
            stability_digest=self.stability_digest_mock,
            anomaly_visualizer=self.anomaly_visualizer_mock
        )

    def test_export_json_report_success(self):
        rand_metric_key = uuid.uuid4().hex
        rand_metric_val = random.randint(100, 999)
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex
        output_path = f"{uuid.uuid4().hex}.json"

        self.anomaly_visualizer_mock.get_summary_metrics.return_value = {rand_metric_key: rand_metric_val}
        self.anomaly_visualizer_mock.render_text.return_value = rand_text
        self.anomaly_visualizer_mock.render_ascii_correlation_graph.return_value = rand_ascii

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result_path = self.exporter.export_json_report(output_path)
            self.assertEqual(result_path, output_path)
            mock_file.assert_called_once_with(output_path, 'w', encoding='utf-8')

            written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_metric_key], rand_metric_val)
            self.assertEqual(parsed_json['text_report'], rand_text)
            self.assertEqual(parsed_json['ascii_graph'], rand_ascii)

    def test_export_json_report_raises_exporter_error(self):
        output_path = f"{uuid.uuid4().hex}.json"
        rand_error_msg = uuid.uuid4().hex
        self.anomaly_visualizer_mock.get_summary_metrics.side_effect = Exception(rand_error_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_json_report(output_path)
        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_export_html_report_success(self):
        rand_metric = uuid.uuid4().hex
        rand_text = uuid.uuid4().hex
        rand_ascii = uuid.uuid4().hex
        output_path = f"{uuid.uuid4().hex}.html"

        self.anomaly_visualizer_mock.get_summary_metrics.return_value = rand_metric
        self.anomaly_visualizer_mock.render_text.return_value = rand_text
        self.anomaly_visualizer_mock.render_ascii_correlation_graph.return_value = rand_ascii

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result_path = self.exporter.export_html_report(output_path)
            self.assertEqual(result_path, output_path)
            mock_file.assert_called_once_with(output_path, 'w', encoding='utf-8')

            written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
            self.assertIn(rand_metric, written_content)
            self.assertIn(rand_text, written_content)
            self.assertIn(rand_ascii, written_content)

    def test_export_html_report_raises_exporter_error(self):
        output_path = f"{uuid.uuid4().hex}.html"
        rand_error_msg = uuid.uuid4().hex
        self.anomaly_visualizer_mock.render_text.side_effect = Exception(rand_error_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_html_report(output_path)
        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_export_stream_to_json_success(self):
        stream_id = uuid.uuid4().hex
        output_path = f"{uuid.uuid4().hex}.json"
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex
        stream_data = {rand_key: rand_val}

        self.stability_digest_mock.export_digest_stream.return_value = stream_data

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result_path = self.exporter.export_stream_to_json(stream_id, output_path)
            self.assertEqual(result_path, output_path)
            self.stability_digest_mock.export_digest_stream.assert_called_once_with(stream_id)

            written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_key], rand_val)

    def test_export_stream_to_json_raises_exporter_error(self):
        stream_id = uuid.uuid4().hex
        output_path = f"{uuid.uuid4().hex}.json"
        rand_error_msg = uuid.uuid4().hex
        self.stability_digest_mock.export_digest_stream.side_effect = Exception(rand_error_msg)

        with self.assertRaises(DigestExporterError) as ctx:
            self.exporter.export_stream_to_json(stream_id, output_path)
        self.assertIn(rand_error_msg, str(ctx.exception))

    def test_export_to_json_adapter_success(self):
        output_path = f"{uuid.uuid4().hex}.json"
        rand_key = uuid.uuid4().hex
        rand_val = random.randint(1, 1000)

        self.anomaly_visualizer_mock.digest = {rand_key: rand_val}

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result_path = self.exporter.export_to_json(output_path)
            self.assertEqual(result_path, output_path)

            written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json[rand_key], rand_val)

    def test_export_to_json_adapter_empty_fallback(self):
        output_path = f"{uuid.uuid4().hex}.json"
        self.exporter.visualizer = None

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result_path = self.exporter.export_to_json(output_path)
            self.assertEqual(result_path, output_path)

            written_data = "".join(call.args[0] for call in mock_file().write.call_args_list)
            parsed_json = json.loads(written_data)
            self.assertEqual(parsed_json, {})

    def test_export_to_html_adapter_success(self):
        output_path = f"{uuid.uuid4().hex}.html"
        rand_key = uuid.uuid4().hex
        rand_val = uuid.uuid4().hex

        self.anomaly_visualizer_mock.digest = {rand_key: rand_val}

        with patch("builtins.open", new_callable=unittest.mock.mock_open) as mock_file:
            result_path = self.exporter.export_to_html(output_path)
            self.assertEqual(result_path, output_path)

            written_content = "".join(call.args[0] for call in mock_file().write.call_args_list)
            self.assertIn(rand_key, written_content)
            self.assertIn(rand_val, written_content)

    def test_export_to_html_adapter_raises_exporter_error(self):
        output_path = f"{uuid.uuid4().hex}.html"
        self.exporter.visualizer = "invalid_visualizer_object"

        with patch("builtins.open", side_effect=IOError(uuid.uuid4().hex)):
            with self.assertRaises(DigestExporterError):
                self.exporter.export_to_html(output_path)


if __name__ == '__main__':
    unittest.main()